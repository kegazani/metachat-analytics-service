from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from src.config import Config

Base = declarative_base()

class Database:
    def __init__(self, config: Config):
        self.config = config
        self.engine = create_async_engine(
            config.database_url,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow,
            echo=False
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    
    async def close(self):
        await self.engine.dispose()

