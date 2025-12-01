from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    
    service_name: str = "analytics-service"
    log_level: str = "INFO"
    
    http_port: int = 8002
    http_host: str = "0.0.0.0"
    
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/metachat_analytics"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    kafka_brokers: List[str] = ["localhost:9092"]
    kafka_consumer_group: str = "analytics-service"
    mood_analyzed_topic: str = "metachat.mood.analyzed"
    diary_entry_created_topic: str = "metachat.diary.entry.created"
    diary_entry_deleted_topic: str = "metachat.diary.entry.deleted"
    archetype_updated_topic: str = "metachat.archetype.updated"

