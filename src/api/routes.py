from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel

from src.api.app import app_state

router = APIRouter()


class DailyMoodResponse(BaseModel):
    id: str
    user_id: str
    date: date
    emotion_vector: List[float]
    dominant_emotion: str
    average_valence: float
    average_arousal: float
    entry_count: int
    total_tokens: int
    topics: Optional[List[str]]
    volatility_index: Optional[float]


@router.get("/users/{user_id}/mood/daily", response_model=List[DailyMoodResponse])
async def get_daily_mood(
    user_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    try:
        db = app_state.get("db")
        repository = app_state.get("repository")
        
        if not db or not repository:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        async for session in db.get_session():
            try:
                summaries = await repository.get_daily_summaries(session, user_id, start_date, end_date)
                return [
                    DailyMoodResponse(
                        id=s.id,
                        user_id=s.user_id,
                        date=s.date,
                        emotion_vector=s.emotion_vector,
                        dominant_emotion=s.dominant_emotion,
                        average_valence=s.average_valence,
                        average_arousal=s.average_arousal,
                        entry_count=s.entry_count,
                        total_tokens=s.total_tokens,
                        topics=s.topics,
                        volatility_index=s.volatility_index
                    )
                    for s in summaries
                ]
            finally:
                await session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/mood/weekly")
async def get_weekly_mood(user_id: str, weeks: int = Query(4, ge=1, le=52)):
    return {"message": "Not implemented yet"}


@router.get("/users/{user_id}/mood/monthly")
async def get_monthly_mood(user_id: str, months: int = Query(6, ge=1, le=24)):
    return {"message": "Not implemented yet"}


@router.get("/users/{user_id}/summary")
async def get_user_summary(user_id: str):
    return {"message": "Not implemented yet"}


@router.get("/users/{user_id}/topics")
async def get_user_topics(user_id: str, period_days: int = Query(30, ge=1, le=365)):
    return {"message": "Not implemented yet"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-service"}

