import asyncio
import sys
import os
from pathlib import Path
from concurrent import futures

import grpc
from grpc import aio
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent / "proto" / "generated"))

from src.config import Config
from src.infrastructure.database import Database
from src.infrastructure.repository import AnalyticsRepository

logger = structlog.get_logger()

try:
    from analytics_pb2 import GetUserStatisticsRequest, GetUserStatisticsResponse
    from analytics_pb2_grpc import AnalyticsServiceServicer, add_AnalyticsServiceServicer_to_server
except ImportError:
    logger.warning("Proto files not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/analytics.proto")
    sys.exit(1)


class AnalyticsServiceServicerImpl(AnalyticsServiceServicer):
    def __init__(self, repository: AnalyticsRepository, db: Database):
        self.repository = repository
        self.db = db
    
    async def GetUserStatistics(self, request: GetUserStatisticsRequest, context) -> GetUserStatisticsResponse:
        try:
            user_id = request.user_id
            logger.info("Getting user statistics", user_id=user_id)
            
            async for session in self.db.get_session():
                try:
                    stats = await self.repository.get_user_statistics(session, user_id)
                    if not stats:
                        context.set_code(grpc.StatusCode.NOT_FOUND)
                        context.set_details("User not found")
                        return GetUserStatisticsResponse()
                    
                    from google.protobuf.timestamp_pb2 import Timestamp
                    from datetime import datetime
                    
                    profile_created_at = Timestamp()
                    profile_created_at.FromDatetime(stats["profile_created_at"])
                    
                    last_personality_update = Timestamp()
                    last_personality_update.FromDatetime(stats["last_personality_update"])
                    
                    return GetUserStatisticsResponse(
                        total_diary_entries=stats["total_diary_entries"],
                        total_mood_analyses=stats["total_mood_analyses"],
                        total_tokens=stats["total_tokens"],
                        dominant_emotion=stats["dominant_emotion"],
                        top_topics=stats["top_topics"],
                        profile_created_at=profile_created_at,
                        last_personality_update=last_personality_update
                    )
                finally:
                    await session.close()
        except Exception as e:
            logger.error("Error getting user statistics", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return GetUserStatisticsResponse()


async def serve():
    config = Config()
    
    db = Database(config.database_url)
    await db.initialize()
    
    repository = AnalyticsRepository(db)
    
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    servicer = AnalyticsServiceServicerImpl(repository, db)
    add_AnalyticsServiceServicer_to_server(servicer, server)
    
    grpc_port = config.grpc_port
    listen_addr = f'0.0.0.0:{grpc_port}'
    server.add_insecure_port(listen_addr)
    
    logger.info("Starting gRPC server", port=grpc_port)
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(5)


if __name__ == '__main__':
    asyncio.run(serve())

