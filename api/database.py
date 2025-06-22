"""
Database connection and configuration
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    client: Optional[AsyncIOMotorClient] = None
    sync_client: Optional[MongoClient] = None


db = Database()


async def get_database():
    """Get async database instance"""
    return db.client


def get_sync_database():
    """Get sync database instance for APScheduler"""
    return db.sync_client


async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/mailwebhooks")
    
    try:
        logger.info(f"Connecting to MongoDB: {mongodb_url}")
        
        # Async client for FastAPI
        db.client = AsyncIOMotorClient(
            mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        
        # Sync client for APScheduler
        db.sync_client = MongoClient(
            mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        db.sync_client.admin.command('ping')
        
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    try:
        if db.client:
            db.client.close()
        if db.sync_client:
            db.sync_client.close()
        logger.info("Disconnected from MongoDB")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Get collection names from environment
        webhooks_collection = os.getenv("WEBHOOKS_COLLECTION", "webhooks")
        jobs_collection = os.getenv("JOBS_COLLECTION", "jobs")
        logs_collection = os.getenv("LOGS_COLLECTION", "logs")
        
        database = db.client.get_default_database()
        
        # Webhooks indexes
        webhooks = database[webhooks_collection]
        await webhooks.create_index("email_address")
        await webhooks.create_index("enabled")
        await webhooks.create_index("trigger_type")
        await webhooks.create_index([("created_at", -1)])
        
        # Jobs indexes
        jobs = database[jobs_collection]
        await jobs.create_index("webhook_id")
        await jobs.create_index("status")
        await jobs.create_index("scheduled_at")
        await jobs.create_index([("created_at", -1)])
        
        # Logs indexes
        logs = database[logs_collection]
        await logs.create_index("webhook_id")
        await logs.create_index("level")
        await logs.create_index([("timestamp", -1)])
        await logs.create_index("job_id", sparse=True)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")


def get_collection_name(collection_type: str) -> str:
    """Get collection name from environment variables"""
    collection_map = {
        "webhooks": os.getenv("WEBHOOKS_COLLECTION", "webhooks"),
        "jobs": os.getenv("JOBS_COLLECTION", "jobs"),
        "logs": os.getenv("LOGS_COLLECTION", "logs")
    }
    return collection_map.get(collection_type, collection_type)
