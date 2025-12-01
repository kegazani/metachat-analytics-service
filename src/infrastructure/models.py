from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Date, Index
from sqlalchemy.sql import func
from datetime import datetime

from src.infrastructure.database import Base


class DailyMoodSummary(Base):
    __tablename__ = "daily_mood_summary"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False)
    emotion_vector = Column(JSON, nullable=False)
    dominant_emotion = Column(String, nullable=False)
    average_valence = Column(Float, nullable=False)
    average_arousal = Column(Float, nullable=False)
    entry_count = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    topics = Column(JSON, nullable=True)
    volatility_index = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_daily_mood_user_date", "user_id", "date", unique=True),
    )


class WeeklyMoodSummary(Base):
    __tablename__ = "weekly_mood_summary"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    emotion_vector = Column(JSON, nullable=False)
    dominant_emotion = Column(String, nullable=False)
    average_valence = Column(Float, nullable=False)
    average_arousal = Column(Float, nullable=False)
    entry_count = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    volatility = Column(Float, nullable=True)
    trend = Column(String, nullable=True)
    most_emotional_day = Column(String, nullable=True)
    most_productive_day = Column(String, nullable=True)
    key_topics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_weekly_mood_user_year_week", "user_id", "year", "week", unique=True),
    )


class MonthlyMoodSummary(Base):
    __tablename__ = "monthly_mood_summary"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    emotion_vector = Column(JSON, nullable=False)
    dominant_emotion = Column(String, nullable=False)
    average_valence = Column(Float, nullable=False)
    average_arousal = Column(Float, nullable=False)
    entry_count = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    volatility = Column(Float, nullable=True)
    trend = Column(String, nullable=True)
    active_days = Column(Integer, nullable=False, default=0)
    average_entries_per_day = Column(Float, nullable=True)
    dominant_topics = Column(JSON, nullable=True)
    archetype_change = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_monthly_mood_user_year_month", "user_id", "year", "month", unique=True),
    )


class UserTopicsSummary(Base):
    __tablename__ = "user_topics_summary"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False, default=0)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_user_topics_user_topic", "user_id", "topic", unique=True),
    )


class ArchetypeHistory(Base):
    __tablename__ = "archetype_history"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    archetype = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_archetype_history_user_changed", "user_id", "changed_at"),
    )

