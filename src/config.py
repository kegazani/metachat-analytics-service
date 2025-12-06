import os
import yaml
from pathlib import Path
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config(config_path: str = "config.yaml") -> dict:
    config_file = Path(config_path)
    if not config_file.exists():
        config_file = Path(__file__).parent.parent / config_path
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=(),
        extra="allow"
    )
    
    def __init__(self, **kwargs):
        yaml_config = load_yaml_config()
        
        if yaml_config:
            service_config = yaml_config.get("service", {})
            server_config = yaml_config.get("server", {})
            database_config = yaml_config.get("database", {})
            kafka_config = yaml_config.get("kafka", {})
            
            kwargs.setdefault("service_name", service_config.get("name", "analytics-service"))
            kwargs.setdefault("log_level", service_config.get("log_level", "INFO"))
            kwargs.setdefault("http_port", server_config.get("http_port", 8002))
            kwargs.setdefault("http_host", server_config.get("http_host", "0.0.0.0"))
            kwargs.setdefault("grpc_port", server_config.get("grpc_port", 50057))
            kwargs.setdefault("database_url", database_config.get("url", "postgresql+asyncpg://postgres:postgres@localhost:5432/metachat_analytics"))
            kwargs.setdefault("database_pool_size", database_config.get("pool_size", 10))
            kwargs.setdefault("database_max_overflow", database_config.get("max_overflow", 20))
            kwargs.setdefault("kafka_brokers", kafka_config.get("brokers", ["localhost:9092"]))
            kwargs.setdefault("kafka_consumer_group", kafka_config.get("consumer_group", "analytics-service"))
            
            topics = kafka_config.get("topics", {})
            kwargs.setdefault("mood_analyzed_topic", topics.get("mood_analyzed", "metachat.mood.analyzed"))
            kwargs.setdefault("diary_entry_created_topic", topics.get("diary_entry_created", "metachat.diary.entry.created"))
            kwargs.setdefault("diary_entry_deleted_topic", topics.get("diary_entry_deleted", "metachat.diary.entry.deleted"))
            kwargs.setdefault("archetype_updated_topic", topics.get("archetype_updated", "metachat.archetype.updated"))
        
        super().__init__(**kwargs)
    
    service_name: str = "analytics-service"
    log_level: str = "INFO"
    
    http_port: int = 8002
    http_host: str = "0.0.0.0"
    grpc_port: int = 50057
    
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/metachat_analytics"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    kafka_brokers: List[str] = ["localhost:9092"]
    kafka_consumer_group: str = "analytics-service"
    
    @model_validator(mode='after')
    def fix_localhost_addresses(self):
        if "localhost" in self.database_url:
            object.__setattr__(self, 'database_url', self.database_url.replace("localhost", "127.0.0.1"))
        
        if self.kafka_brokers:
            new_brokers = [broker.replace("localhost", "127.0.0.1") if "localhost" in broker else broker for broker in self.kafka_brokers]
            object.__setattr__(self, 'kafka_brokers', new_brokers)
        
        return self
    
    mood_analyzed_topic: str = "metachat.mood.analyzed"
    diary_entry_created_topic: str = "metachat.diary.entry.created"
    diary_entry_deleted_topic: str = "metachat.diary.entry.deleted"
    archetype_updated_topic: str = "metachat.archetype.updated"
    
    all_kafka_topics: dict = {
        "user_service": ["metachat-user-events"],
        "diary_service": [
            "diary-events",
            "session-events",
            "metachat.diary.entry.created",
            "metachat.diary.entry.updated",
            "metachat.diary.entry.deleted"
        ],
        "mood_analysis_service": [
            "metachat.diary.entry.created",
            "metachat.diary.entry.updated",
            "metachat.mood.analyzed",
            "metachat.mood.analysis.failed"
        ],
        "analytics_service": [
            "metachat.mood.analyzed",
            "metachat.diary.entry.created",
            "metachat.diary.entry.deleted",
            "metachat.archetype.updated"
        ],
        "archetype_service": [
            "metachat.mood.analyzed",
            "metachat.diary.entry.created",
            "metachat.archetype.assigned",
            "metachat.archetype.updated",
            "metachat.archetype.calculation.triggered"
        ],
        "biometric_service": ["metachat.biometric.data.received"],
        "correlation_service": [
            "metachat.mood.analyzed",
            "metachat.biometric.data.received",
            "metachat.correlation.discovered"
        ]
    }

