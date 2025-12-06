from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import structlog

from src.config import Config
from src.infrastructure.database import Database, Base
from src.infrastructure.models import DailyMoodSummary, WeeklyMoodSummary, MonthlyMoodSummary, UserTopicsSummary, ArchetypeHistory
from src.infrastructure.repository import AnalyticsRepository
from src.infrastructure.kafka_client import KafkaConsumer
from src.application.event_handler import EventHandler
from src.api.state import app_state, consumer_task
from src.api.routes import router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    
    db = Database(config)
    
    await db.create_database_if_not_exists()
    await db.create_tables()
    
    repository = AnalyticsRepository(db)
    
    event_handler = EventHandler(repository, db)
    kafka_consumer = KafkaConsumer(config, event_handler.handle_message)
    kafka_consumer.start()
    
    app_state["config"] = config
    app_state["db"] = db
    app_state["repository"] = repository
    app_state["kafka_consumer"] = kafka_consumer
    
    import src.api.state as state_module
    state_module.consumer_task = asyncio.create_task(kafka_consumer.consume_loop())
    
    logger.info("Analytics Service started")
    
    yield
    
    import src.api.state as state_module
    if state_module.consumer_task:
        state_module.consumer_task.cancel()
        try:
            await state_module.consumer_task
        except asyncio.CancelledError:
            pass
    
    kafka_consumer.stop()
    await db.close()


app = FastAPI(
    title="Analytics Service",
    description="Service for mood analytics and aggregation",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "analytics-service", "version": "1.0.0"}

