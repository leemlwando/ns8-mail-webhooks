#!/usr/bin/env python3
"""
Mail Webhooks API Server
FastAPI application for managing mail webhooks with configurable MongoDB connection
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, validator
from pymongo import MongoClient
from bson import ObjectId
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class WebhookBase(BaseModel):
    name: str
    url: HttpUrl
    api_key: Optional[str] = ""
    payload_type: str
    trigger_type: str
    interval: Optional[int] = 60
    mailboxes: Optional[List[str]] = []
    filters: Optional[Dict[str, Any]] = {}
    active: Optional[bool] = True

    @validator('payload_type')
    def validate_payload_type(cls, v):
        if v not in ['RAW', 'JSON']:
            raise ValueError('payload_type must be RAW or JSON')
        return v

    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        if v not in ['realtime', 'interval']:
            raise ValueError('trigger_type must be realtime or interval')
        return v

class WebhookCreate(WebhookBase):
    pass

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    payload_type: Optional[str] = None
    trigger_type: Optional[str] = None
    interval: Optional[int] = None
    mailboxes: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

class WebhookResponse(WebhookBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None

class Settings(BaseModel):
    mongodb_url: str
    mail_server_uuid: Optional[str] = ""
    mail_domain: Optional[str] = ""
    max_retries: Optional[int] = 3
    retry_delay: Optional[int] = 60
    # Collection names - customizable
    webhooks_collection: Optional[str] = "webhooks"
    events_collection: Optional[str] = "events"
    settings_collection: Optional[str] = "settings"
    triggers_collection: Optional[str] = "triggers"
    logs_collection: Optional[str] = "logs"

class TestResult(BaseModel):
    success: bool
    status_code: int
    response_time: float
    response_body: Optional[str] = None
    error: Optional[str] = None

# Global variables
mongodb_client = None
db = None
current_settings = None

def get_collection_names():
    """Get collection names from environment variables, settings, or use defaults"""
    global current_settings
    
    # Priority: environment variables -> settings -> defaults
    collection_names = {
        'webhooks': os.getenv('WEBHOOKS_COLLECTION') or 'webhooks',
        'events': os.getenv('EVENTS_COLLECTION') or 'events',
        'settings': os.getenv('SETTINGS_COLLECTION') or 'settings',
        'triggers': os.getenv('TRIGGERS_COLLECTION') or 'triggers',
        'logs': os.getenv('LOGS_COLLECTION') or 'logs'
    }
    
    # Override with settings if available
    if current_settings:
        collection_names['webhooks'] = current_settings.get('webhooks_collection', collection_names['webhooks'])
        collection_names['events'] = current_settings.get('events_collection', collection_names['events'])
        collection_names['settings'] = current_settings.get('settings_collection', collection_names['settings'])
        collection_names['triggers'] = current_settings.get('triggers_collection', collection_names['triggers'])
        collection_names['logs'] = current_settings.get('logs_collection', collection_names['logs'])
    
    return collection_names

def get_collection(collection_type: str):
    """Get a collection by type using current settings"""
    if db is None:
        raise Exception("Database not connected")
    
    collection_names = get_collection_names()
    collection_name = collection_names.get(collection_type)
    if not collection_name:
        raise Exception(f"Unknown collection type: {collection_type}")
    
    return db[collection_name]

def load_current_settings():
    """Load current settings from database"""
    global current_settings
    try:
        if db is not None:
            # Use environment variable or default for settings collection name
            settings_collection_name = os.getenv('SETTINGS_COLLECTION', 'settings')
            settings_coll = db[settings_collection_name]
            current_settings = settings_coll.find_one() or {}
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
        current_settings = {}

def get_mongodb_url():
    """Get MongoDB URL from environment"""
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        raise Exception("MONGODB_URL environment variable is required")
    return mongodb_url

def connect_to_mongodb(mongodb_url: str = None):
    """Connect to MongoDB with given URL"""
    global mongodb_client, db
    
    url = mongodb_url or get_mongodb_url()
    try:
        mongodb_client = MongoClient(url, serverSelectionTimeoutMS=5000)
        # Test connection
        mongodb_client.admin.command('ping')
        db = mongodb_client.mailwebhooks
        logger.info(f"Connected to MongoDB successfully at {url[:20]}...")
        
        # Load current settings to get collection names
        load_current_settings()
        
        # Create indexes on all collections using current settings
        collection_names = get_collection_names()
        
        # Webhooks collection indexes
        db[collection_names['webhooks']].create_index("name")
        db[collection_names['webhooks']].create_index("active")
        
        # Events collection indexes
        db[collection_names['events']].create_index("timestamp")
        db[collection_names['events']].create_index("webhook_id")
        
        # Triggers collection indexes
        db[collection_names['triggers']].create_index("webhook_id")
        db[collection_names['triggers']].create_index("next_run")
        
        # Logs collection indexes
        db[collection_names['logs']].create_index("timestamp")
        db[collection_names['logs']].create_index("webhook_id")
        db[collection_names['logs']].create_index("status")
        
        logger.info("Database indexes ensured")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        db = None
        mongodb_client = None
        return False

def serialize_objectid(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_objectid(item) for item in obj]
    return obj

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        if connect_to_mongodb():
            logger.info("Mail Webhooks API started successfully")
        else:
            logger.warning("Started without MongoDB connection - configure via settings")
    except Exception as e:
        logger.warning(f"Started without MongoDB connection: {e}")
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()
    logger.info("Mail Webhooks API stopped")

# Create FastAPI app
app = FastAPI(
    title="Mail Webhooks API",
    description="API for managing mail webhooks",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db is None:
            raise Exception("Database not connected")
        
        # Test MongoDB connection
        db.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mongodb": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/api/webhooks", response_model=List[WebhookResponse])
async def list_webhooks():
    """List all webhooks"""
    try:
        webhooks_coll = get_collection('webhooks')
        webhooks = list(webhooks_coll.find())
        result = []
        for webhook in webhooks:
            webhook_dict = serialize_objectid(webhook)
            webhook_dict['id'] = webhook_dict.pop('_id')
            result.append(webhook_dict)
        return result
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(webhook: WebhookCreate):
    """Create a new webhook"""
    try:
        webhooks_coll = get_collection('webhooks')
        
        # Create webhook document
        webhook_doc = {
            **webhook.dict(),
            'url': str(webhook.url),  # Convert HttpUrl to string
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_triggered': None
        }
        
        result = webhooks_coll.insert_one(webhook_doc)
        webhook_doc['_id'] = result.inserted_id
        
        # Prepare response
        response_dict = serialize_objectid(webhook_doc)
        response_dict['id'] = response_dict.pop('_id')
        
        logger.info(f"Created webhook: {webhook.name}")
        return response_dict
        
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str):
    """Get webhook by ID"""
    try:
        webhooks_coll = get_collection('webhooks')
        webhook = webhooks_coll.find_one({"_id": ObjectId(webhook_id)})
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        response_dict = serialize_objectid(webhook)
        response_dict['id'] = response_dict.pop('_id')
        return response_dict
    except Exception as e:
        logger.error(f"Error getting webhook {webhook_id}: {e}")
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid webhook ID")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: str, webhook_update: WebhookUpdate):
    """Update webhook"""
    try:
        webhooks_coll = get_collection('webhooks')
        
        # Prepare update data
        update_data = {k: v for k, v in webhook_update.dict().items() if v is not None}
        if 'url' in update_data:
            update_data['url'] = str(update_data['url'])  # Convert HttpUrl to string
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        result = webhooks_coll.update_one(
            {"_id": ObjectId(webhook_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Return updated webhook
        webhook = webhooks_coll.find_one({"_id": ObjectId(webhook_id)})
        response_dict = serialize_objectid(webhook)
        response_dict['id'] = response_dict.pop('_id')
        
        logger.info(f"Updated webhook: {webhook_id}")
        return response_dict
        
    except Exception as e:
        logger.error(f"Error updating webhook {webhook_id}: {e}")
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid webhook ID")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete webhook"""
    try:
        webhooks_coll = get_collection('webhooks')
        result = webhooks_coll.delete_one({"_id": ObjectId(webhook_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        logger.info(f"Deleted webhook: {webhook_id}")
        return {"message": "Webhook deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting webhook {webhook_id}: {e}")
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid webhook ID")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/{webhook_id}/test", response_model=TestResult)
async def test_webhook(webhook_id: str):
    """Test webhook with sample payload"""
    try:
        webhooks_coll = get_collection('webhooks')
        webhook = webhooks_coll.find_one({"_id": ObjectId(webhook_id)})
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Create test payload
        test_payload = {
            "test": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_id": webhook_id,
            "message": "This is a test webhook from Mail Webhooks module"
        }
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if webhook.get('api_key'):
            headers['Authorization'] = f"Bearer {webhook['api_key']}"
        
        # Send test webhook
        response = requests.post(
            webhook['url'],
            json=test_payload,
            headers=headers,
            timeout=10
        )
        
        result = TestResult(
            success=response.status_code < 400,
            status_code=response.status_code,
            response_time=response.elapsed.total_seconds(),
            response_body=response.text[:500] if response.text else None
        )
        
        logger.info(f"Tested webhook {webhook_id}: {result.status_code}")
        return result
        
    except requests.RequestException as e:
        logger.error(f"Error testing webhook {webhook_id}: {e}")
        return TestResult(
            success=False,
            status_code=0,
            response_time=0.0,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing webhook {webhook_id}: {e}")
        if "not a valid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid webhook ID")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    """Get module settings"""
    try:
        settings_coll = get_collection('settings')
        settings = settings_coll.find_one() or {}
        settings.pop('_id', None)
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/settings")
async def update_settings(settings: Settings):
    """Update module settings"""
    try:
        settings_coll = get_collection('settings')
        settings_dict = settings.dict()
        settings_dict['updated_at'] = datetime.now(timezone.utc)
        
        # If MongoDB URL changed, reconnect
        current_settings = settings_coll.find_one() or {}
        if current_settings.get('mongodb_url') != settings.mongodb_url:
            logger.info("MongoDB URL changed, reconnecting...")
            connect_to_mongodb(settings.mongodb_url)
        
        settings_coll.replace_one({}, settings_dict, upsert=True)
        
        # Reload current settings to update collection names
        load_current_settings()
        
        logger.info("Settings updated")
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def list_events(limit: int = 50):
    """List recent mail events"""
    try:
        events_coll = get_collection('events')
        events = list(events_coll.find().sort("timestamp", -1).limit(limit))
        return serialize_objectid(events)
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
