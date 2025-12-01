from typing import List, Dict
from datetime import date, datetime, timedelta
import numpy as np
from collections import Counter

import structlog

logger = structlog.get_logger()


class MoodAggregator:
    @staticmethod
    def calculate_daily_aggregate(analyses: List[Dict]) -> Dict:
        if not analyses:
            return {}
        
        emotion_vectors = [a.get("emotion_vector", [0.0] * 8) for a in analyses]
        valences = [a.get("valence", 0.0) for a in analyses]
        arousals = [a.get("arousal", 0.0) for a in analyses]
        topics = []
        for a in analyses:
            topics.extend(a.get("detected_topics", []))
        
        avg_emotion_vector = np.mean(emotion_vectors, axis=0).tolist()
        dominant_idx = np.argmax(avg_emotion_vector)
        emotion_names = ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]
        dominant_emotion = emotion_names[dominant_idx] if dominant_idx < len(emotion_names) else "neutral"
        
        volatility = np.std(valences) if len(valences) > 1 else 0.0
        
        topic_counts = Counter(topics)
        top_topics = [topic for topic, _ in topic_counts.most_common(5)]
        
        return {
            "emotion_vector": avg_emotion_vector,
            "dominant_emotion": dominant_emotion,
            "average_valence": np.mean(valences),
            "average_arousal": np.mean(arousals),
            "entry_count": len(analyses),
            "total_tokens": sum(a.get("tokens_count", 0) for a in analyses),
            "topics": top_topics,
            "volatility_index": volatility
        }
    
    @staticmethod
    def calculate_weekly_aggregate(daily_summaries: List[Dict]) -> Dict:
        if not daily_summaries:
            return {}
        
        emotion_vectors = [d.get("emotion_vector", [0.0] * 8) for d in daily_summaries]
        valences = [d.get("average_valence", 0.0) for d in daily_summaries]
        
        avg_emotion_vector = np.mean(emotion_vectors, axis=0).tolist()
        dominant_idx = np.argmax(avg_emotion_vector)
        emotion_names = ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]
        dominant_emotion = emotion_names[dominant_idx] if dominant_idx < len(emotion_names) else "neutral"
        
        volatility = np.std(valences) if len(valences) > 1 else 0.0
        
        if len(valences) >= 2:
            trend = "improving" if valences[-1] > valences[0] else "declining" if valences[-1] < valences[0] else "stable"
        else:
            trend = "stable"
        
        most_emotional_day = max(daily_summaries, key=lambda x: abs(x.get("average_valence", 0.0))) if daily_summaries else None
        most_productive_day = max(daily_summaries, key=lambda x: x.get("entry_count", 0)) if daily_summaries else None
        
        all_topics = []
        for d in daily_summaries:
            all_topics.extend(d.get("topics", []))
        topic_counts = Counter(all_topics)
        key_topics = [topic for topic, _ in topic_counts.most_common(5)]
        
        return {
            "emotion_vector": avg_emotion_vector,
            "dominant_emotion": dominant_emotion,
            "average_valence": np.mean(valences),
            "average_arousal": np.mean([d.get("average_arousal", 0.0) for d in daily_summaries]),
            "entry_count": sum(d.get("entry_count", 0) for d in daily_summaries),
            "total_tokens": sum(d.get("total_tokens", 0) for d in daily_summaries),
            "volatility": volatility,
            "trend": trend,
            "most_emotional_day": most_emotional_day.get("date").isoformat() if most_emotional_day else None,
            "most_productive_day": most_productive_day.get("date").isoformat() if most_productive_day else None,
            "key_topics": key_topics
        }
    
    @staticmethod
    def calculate_monthly_aggregate(weekly_summaries: List[Dict]) -> Dict:
        if not weekly_summaries:
            return {}
        
        emotion_vectors = [w.get("emotion_vector", [0.0] * 8) for w in weekly_summaries]
        valences = [w.get("average_valence", 0.0) for w in weekly_summaries]
        
        avg_emotion_vector = np.mean(emotion_vectors, axis=0).tolist()
        dominant_idx = np.argmax(avg_emotion_vector)
        emotion_names = ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]
        dominant_emotion = emotion_names[dominant_idx] if dominant_idx < len(emotion_names) else "neutral"
        
        volatility = np.std(valences) if len(valences) > 1 else 0.0
        
        if len(valences) >= 2:
            trend = "improving" if valences[-1] > valences[0] else "declining" if valences[-1] < valences[0] else "stable"
        else:
            trend = "stable"
        
        all_topics = []
        for w in weekly_summaries:
            all_topics.extend(w.get("key_topics", []))
        topic_counts = Counter(all_topics)
        dominant_topics = [topic for topic, _ in topic_counts.most_common(5)]
        
        active_days = len([w for w in weekly_summaries if w.get("entry_count", 0) > 0])
        total_entries = sum(w.get("entry_count", 0) for w in weekly_summaries)
        avg_entries_per_day = total_entries / 30.0 if active_days > 0 else 0.0
        
        return {
            "emotion_vector": avg_emotion_vector,
            "dominant_emotion": dominant_emotion,
            "average_valence": np.mean(valences),
            "average_arousal": np.mean([w.get("average_arousal", 0.0) for w in weekly_summaries]),
            "entry_count": total_entries,
            "total_tokens": sum(w.get("total_tokens", 0) for w in weekly_summaries),
            "volatility": volatility,
            "trend": trend,
            "active_days": active_days,
            "average_entries_per_day": avg_entries_per_day,
            "dominant_topics": dominant_topics
        }
    
    @staticmethod
    def get_week_number(d: date) -> tuple[int, int]:
        year, week, _ = d.isocalendar()
        return year, week
    
    @staticmethod
    def get_month_number(d: date) -> tuple[int, int]:
        return d.year, d.month

