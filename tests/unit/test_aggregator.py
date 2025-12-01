import pytest
from src.domain.aggregator import MoodAggregator


def test_calculate_daily_aggregate():
    analyses = [
        {
            "emotion_vector": [0.8, 0.3, 0.1, 0.2, 0.1, 0.0, 0.1, 0.4],
            "valence": 0.6,
            "arousal": 0.4,
            "tokens_count": 100,
            "detected_topics": ["работа"]
        }
    ]
    
    aggregate = MoodAggregator.calculate_daily_aggregate(analyses)
    
    assert "emotion_vector" in aggregate
    assert "dominant_emotion" in aggregate
    assert aggregate["entry_count"] == 1
    assert aggregate["total_tokens"] == 100

