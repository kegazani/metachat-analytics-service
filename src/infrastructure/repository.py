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

