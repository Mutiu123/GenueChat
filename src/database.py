"""MongoDB connection management with singleton pattern and pooling."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Database:
    """Singleton wrapper around an async Motor MongoDB client.

    Manages connection pooling, health checks, and graceful shutdown.
    """

    _instance: Optional["Database"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Open the MongoDB connection with configured pool sizes."""
        if self._client is not None:
            return
        logger.info(
            "Connecting to MongoDB at %s (pool %d-%d)",
            settings.MONGODB_URL,
            settings.MONGODB_MIN_POOL_SIZE,
            settings.MONGODB_MAX_POOL_SIZE,
        )
        self._client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
            connectTimeoutMS=settings.MONGODB_TIMEOUT_MS,
        )
        self._db = self._client[settings.MONGODB_DATABASE]
        # Verify connectivity
        await self._client.admin.command("ping")
        logger.info("MongoDB connection established")

    async def close(self) -> None:
        """Gracefully close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    async def health_check(self) -> bool:
        """Return True if MongoDB is reachable."""
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False


def get_database() -> Database:
    """Return the singleton Database instance."""
    return Database()
