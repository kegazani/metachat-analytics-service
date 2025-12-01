import json
from typing import Dict, Any, Optional, Callable
from confluent_kafka import Consumer, KafkaException
import structlog

from src.config import Config

logger = structlog.get_logger()


class KafkaConsumer:
    def __init__(self, config: Config, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler
        
        self.consumer_config = {
            'bootstrap.servers': ','.join(config.kafka_brokers),
            'group.id': config.kafka_consumer_group,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        self.consumer = None
        self.running = False
    
    def start(self):
        if self.running:
            return
        
        try:
            self.consumer = Consumer(self.consumer_config)
            topics = [
                self.config.mood_analyzed_topic,
                self.config.diary_entry_created_topic,
                self.config.diary_entry_deleted_topic,
                self.config.archetype_updated_topic
            ]
            self.consumer.subscribe(topics)
            self.running = True
            logger.info("Kafka consumer started", topics=topics)
        except KafkaException as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise
    
    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")
    
    async def consume_loop(self):
        import asyncio
        
        while self.running:
            try:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                
                if msg.error():
                    logger.error("Consumer error", error=str(msg.error()))
                    continue
                
                try:
                    await self._process_message(msg)
                    self.consumer.commit(asynchronous=False)
                except Exception as e:
                    logger.error("Error processing message", error=str(e), exc_info=True)
            except Exception as e:
                logger.error("Error in consume loop", error=str(e), exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_message(self, msg):
        try:
            value = msg.value().decode('utf-8')
            data = json.loads(value)
            topic = msg.topic()
            
            correlation_id = None
            if isinstance(data, dict):
                if "metadata" in data:
                    correlation_id = data["metadata"].get("correlation_id")
                elif "correlation_id" in data:
                    correlation_id = data.get("correlation_id")
            
            await self.message_handler(topic, data, correlation_id)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON", error=str(e))
        except Exception as e:
            logger.error("Error processing message", error=str(e), exc_info=True)

