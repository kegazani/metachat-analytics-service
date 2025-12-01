from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from src.config import Config
from src.infrastructure.database import Database
from src.infrastructure.repository import AnalyticsRepository
from src.infrastructure.kafka_client import KafkaConsumer
from src.application.event_handler import EventHandler
from src.api.routes import router

app_state = {}
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    
    db = Database(config)
    repository = AnalyticsRepository(db)
    
    event_handler = EventHandler(repository, db)
    kafka_consumer = KafkaConsumer(config, event_handler.handle_message)
    kafka_consumer.start()
    
    app_state["config"] = config
    app_state["db"] = db
    app_state["repository"] = repository
    app_state["kafka_consumer"] = kafka_consumer
    
    global consumer_task
    consumer_task = asyncio.create_task(kafka_consumer.consume_loop())
    
    yield
    
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    kafka_consumer.stop()
    await db.close()


app = FastAPI(
    title="Analytics Service",
    description="Service for mood analytics and aggregation",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "analytics-service", "version": "1.0.0"}

