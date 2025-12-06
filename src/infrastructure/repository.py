from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, datetime
import uuid

from src.infrastructure.models import (
    DailyMoodSummary, WeeklyMoodSummary, MonthlyMoodSummary,
    UserTopicsSummary, ArchetypeHistory
)
from src.infrastructure.database import Database


class AnalyticsRepository:
    def __init__(self, db: Database):
        self.db = db
    
    async def get_or_create_daily_summary(
        self, session: AsyncSession, user_id: str, summary_date: date
    ) -> DailyMoodSummary:
        result = await session.execute(
            select(DailyMoodSummary).where(
                and_(
                    DailyMoodSummary.user_id == user_id,
                    DailyMoodSummary.date == summary_date
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        new_summary = DailyMoodSummary(
            id=str(uuid.uuid4()),
            user_id=user_id,
            date=summary_date,
            emotion_vector=[0.0] * 8,
            dominant_emotion="neutral",
            average_valence=0.0,
            average_arousal=0.0,
            entry_count=0,
            total_tokens=0
        )
        session.add(new_summary)
        await session.commit()
        await session.refresh(new_summary)
        return new_summary
    
    async def get_daily_summaries(
        self, session: AsyncSession, user_id: str, start_date: date, end_date: date
    ) -> List[DailyMoodSummary]:
        result = await session.execute(
            select(DailyMoodSummary).where(
                and_(
                    DailyMoodSummary.user_id == user_id,
                    DailyMoodSummary.date >= start_date,
                    DailyMoodSummary.date <= end_date
                )
            ).order_by(DailyMoodSummary.date)
        )
        return list(result.scalars().all())
    
    async def save_archetype_history(
        self, session: AsyncSession, user_id: str, archetype: str,
        confidence: float, model_version: str
    ) -> ArchetypeHistory:
        history = ArchetypeHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            archetype=archetype,
            confidence=confidence,
            model_version=model_version
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)
        return history
    
    async def get_user_statistics(
        self, session: AsyncSession, user_id: str
    ) -> Optional[dict]:
        from sqlalchemy import func
        
        total_diary_entries = await session.execute(
            select(func.count(DailyMoodSummary.id)).where(
                DailyMoodSummary.user_id == user_id
            )
        )
        diary_count = total_diary_entries.scalar() or 0
        
        total_mood_analyses = await session.execute(
            select(func.sum(DailyMoodSummary.entry_count)).where(
                DailyMoodSummary.user_id == user_id
            )
        )
        mood_count = total_mood_analyses.scalar() or 0
        
        total_tokens = await session.execute(
            select(func.sum(DailyMoodSummary.total_tokens)).where(
                DailyMoodSummary.user_id == user_id
            )
        )
        tokens = total_tokens.scalar() or 0
        
        latest_summary = await session.execute(
            select(DailyMoodSummary).where(
                DailyMoodSummary.user_id == user_id
            ).order_by(DailyMoodSummary.date.desc()).limit(1)
        )
        latest = latest_summary.scalar_one_or_none()
        
        dominant_emotion = latest.dominant_emotion if latest else ""
        
        topics_summary = await session.execute(
            select(UserTopicsSummary).where(
                UserTopicsSummary.user_id == user_id
            ).order_by(UserTopicsSummary.frequency.desc()).limit(5)
        )
        topics = topics_summary.scalars().all()
        top_topics = [t.topic for t in topics] if topics else []
        
        first_summary = await session.execute(
            select(DailyMoodSummary).where(
                DailyMoodSummary.user_id == user_id
            ).order_by(DailyMoodSummary.date.asc()).limit(1)
        )
        first = first_summary.scalar_one_or_none()
        profile_created_at = first.date if first else datetime.now()
        
        archetype_history = await session.execute(
            select(ArchetypeHistory).where(
                ArchetypeHistory.user_id == user_id
            ).order_by(ArchetypeHistory.changed_at.desc()).limit(1)
        )
        last_archetype = archetype_history.scalar_one_or_none()
        last_personality_update = last_archetype.changed_at if last_archetype else datetime.now()
        
        return {
            "total_diary_entries": diary_count,
            "total_mood_analyses": mood_count,
            "total_tokens": tokens,
            "dominant_emotion": dominant_emotion,
            "top_topics": top_topics,
            "profile_created_at": profile_created_at,
            "last_personality_update": last_personality_update
        }

