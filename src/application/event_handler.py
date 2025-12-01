from typing import Dict, Any, Optional
from datetime import date, datetime
import structlog

from src.domain.aggregator import MoodAggregator
from src.infrastructure.repository import AnalyticsRepository
from src.infrastructure.database import Database

logger = structlog.get_logger()


class EventHandler:
    def __init__(self, repository: AnalyticsRepository, db: Database):
        self.repository = repository
        self.db = db
        self.aggregator = MoodAggregator()
    
    async def handle_mood_analyzed(self, event_data: Dict[str, Any], correlation_id: Optional[str] = None):
        try:
            payload = event_data.get("payload", {})
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)
            
            user_id = payload.get("user_id")
            entry_id = payload.get("entry_id")
            emotion_vector = payload.get("emotion_vector", [])
            dominant_emotion = payload.get("dominant_emotion", "neutral")
            valence = payload.get("valence", 0.0)
            arousal = payload.get("arousal", 0.0)
            tokens_count = payload.get("tokens_count", 0)
            detected_topics = payload.get("detected_topics", [])
            
            if not user_id:
                return
            
            analysis_data = {
                "emotion_vector": emotion_vector,
                "dominant_emotion": dominant_emotion,
                "valence": valence,
                "arousal": arousal,
                "tokens_count": tokens_count,
                "detected_topics": detected_topics
            }
            
            today = date.today()
            
            async for session in self.db.get_session():
                try:
                    daily_summary = await self.repository.get_or_create_daily_summary(session, user_id, today)
                    
                    existing_analyses = [analysis_data]
                    aggregate = self.aggregator.calculate_daily_aggregate(existing_analyses)
                    
                    daily_summary.emotion_vector = aggregate.get("emotion_vector", emotion_vector)
                    daily_summary.dominant_emotion = aggregate.get("dominant_emotion", dominant_emotion)
                    daily_summary.average_valence = aggregate.get("average_valence", valence)
                    daily_summary.average_arousal = aggregate.get("average_arousal", arousal)
                    daily_summary.entry_count += 1
                    daily_summary.total_tokens += tokens_count
                    daily_summary.topics = aggregate.get("topics", detected_topics)
                    daily_summary.volatility_index = aggregate.get("volatility_index", 0.0)
                    daily_summary.updated_at = datetime.utcnow()
                    
                    await session.commit()
                finally:
                    await session.close()
            
        except Exception as e:
            logger.error("Error processing MoodAnalyzed", error=str(e), exc_info=True)
    
    async def handle_archetype_updated(self, event_data: Dict[str, Any], correlation_id: Optional[str] = None):
        try:
            payload = event_data.get("payload", {})
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)
            
            user_id = payload.get("user_id")
            archetype = payload.get("archetype")
            confidence = payload.get("confidence", 0.0)
            model_version = payload.get("model_version", "unknown")
            
            if not user_id or not archetype:
                return
            
            async for session in self.db.get_session():
                try:
                    await self.repository.save_archetype_history(
                        session, user_id, archetype, confidence, model_version
                    )
                finally:
                    await session.close()
            
        except Exception as e:
            logger.error("Error processing ArchetypeUpdated", error=str(e), exc_info=True)
    
    async def handle_message(self, topic: str, event_data: Dict[str, Any], correlation_id: Optional[str] = None):
        if "mood.analyzed" in topic or "MoodAnalyzed" in topic:
            await self.handle_mood_analyzed(event_data, correlation_id)
        elif "archetype.updated" in topic or "ArchetypeUpdated" in topic:
            await self.handle_archetype_updated(event_data, correlation_id)

