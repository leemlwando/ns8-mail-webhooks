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
import time

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, validator
from pymongo import MongoClient
from bson import ObjectId
import requests

# Import mail monitoring components
from .mail_discovery import MailServerDiscovery
from .imap_integration import IMAPClient
from .mail_monitor import start_mail_monitor, stop_mail_monitor, get_monitor_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced Pydantic models for request/response
class TriggerConfig(BaseModel):
    """Configuration for webhook triggers"""
    trigger_type: str  # 'realtime' or 'interval'
    mailboxes: Optional[List[str]] = []  # Specific mailboxes to monitor
    interval_seconds: Optional[int] = 300  # For interval-based triggers (in seconds)
    interval_expression: Optional[str] = None  # Cron-like expression (future enhancement)
    
    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        if v not in ['realtime', 'interval']:
            raise ValueError('trigger_type must be realtime or interval')
        return v
    
    @validator('interval_seconds')
    def validate_interval_seconds(cls, v, values):
        if values.get('trigger_type') == 'interval' and (v is None or v < 60):
            raise ValueError('interval_seconds must be at least 60 seconds for interval triggers')
        return v

class PostProcessActions(BaseModel):
    """Actions to perform after successful webhook delivery"""
    mark_as_read: Optional[bool] = False  # Mark message as read
    delete_message: Optional[bool] = False  # Delete message after processing
    move_to_folder: Optional[str] = None  # Move to specific folder (e.g., "Processed")
    add_flag: Optional[str] = None  # Add custom flag to message

class MailFilters(BaseModel):
    """Filters for incoming mail processing"""
    sender_patterns: Optional[List[str]] = []  # Email patterns to match senders
    subject_patterns: Optional[List[str]] = []  # Subject line patterns
    body_patterns: Optional[List[str]] = []  # Body content patterns
    has_attachments: Optional[bool] = None  # Filter by attachment presence
    min_size_kb: Optional[int] = None  # Minimum message size
    max_size_kb: Optional[int] = None  # Maximum message size

class WebhookBase(BaseModel):
    name: str
    url: HttpUrl
    api_key: Optional[str] = ""
    payload_type: str
    trigger_config: TriggerConfig
    post_actions: Optional[PostProcessActions] = PostProcessActions()
    mail_filters: Optional[MailFilters] = MailFilters()
    active: Optional[bool] = True

    @validator('payload_type')
    def validate_payload_type(cls, v):
        if v not in ['RAW', 'JSON']:
            raise ValueError('payload_type must be RAW or JSON')
        return v

class WebhookCreate(WebhookBase):
    pass

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    payload_type: Optional[str] = None
    trigger_config: Optional[TriggerConfig] = None
    post_actions: Optional[PostProcessActions] = None
    mail_filters: Optional[MailFilters] = None
    active: Optional[bool] = None
    
    @validator('payload_type')
    def validate_payload_type(cls, v):
        if v is not None and v not in ['RAW', 'JSON']:
            raise ValueError('payload_type must be RAW or JSON')
        return v

class WebhookResponse(WebhookBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None
    execution_count: Optional[int] = 0
    last_execution_status: Optional[str] = None  # 'success', 'failed', 'pending'

class WebhookExecutionLog(BaseModel):
    """Log entry for webhook execution"""
    webhook_id: str
    timestamp: datetime
    status: str  # 'success', 'failed', 'skipped'
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    processed_message_id: Optional[str] = None
    mailbox: Optional[str] = None
    post_actions_applied: Optional[Dict[str, Any]] = {}

class MailEvent(BaseModel):
    """Represents a mail event that triggered a webhook"""
    id: str
    webhook_id: str
    message_id: str
    mailbox: str
    sender: str
    recipient: str
    subject: str
    timestamp: datetime
    size_bytes: Optional[int] = None
    has_attachments: Optional[bool] = False
    processing_status: str  # 'pending', 'processed', 'failed', 'skipped'
    webhook_delivered: Optional[bool] = False
    post_actions_applied: Optional[Dict[str, Any]] = {}

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

# Create FastAPI app with enhanced lifespan
app = FastAPI(
    title="Mail Webhooks API",
    description="API for managing mail webhooks with IMAP integration",
    version="2.0.0",
    lifespan=enhanced_lifespan
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

@app.get("/api/webhooks/{webhook_id}/logs")
async def get_webhook_logs(webhook_id: str, limit: int = 50):
    """Get execution logs for a specific webhook"""
    try:
        logs_coll = get_collection('logs')
        logs = list(logs_coll.find({"webhook_id": webhook_id}).sort("timestamp", -1).limit(limit))
        return serialize_objectid(logs)
    except Exception as e:
        logger.error(f"Error getting webhook logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/{webhook_id}/execute")
async def manual_webhook_execution(webhook_id: str):
    """Manually trigger webhook execution for testing"""
    try:
        # Get webhook configuration
        webhooks_coll = get_collection('webhooks')
        webhook = webhooks_coll.find_one({"_id": ObjectId(webhook_id)})
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        if not webhook.get('active', True):
            raise HTTPException(status_code=400, detail="Webhook is disabled")
        
        # Create a test payload
        test_payload = {
            "test_mode": True,
            "webhook_id": webhook_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Manual webhook execution test"
        }
        
        # Execute webhook
        result = await execute_webhook_delivery(webhook, test_payload, is_test=True)
        
        return {
            "success": result.get('success', False),
            "status_code": result.get('status_code', 0),
            "response_time": result.get('response_time', 0),
            "message": "Webhook executed successfully" if result.get('success') else "Webhook execution failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mailboxes")
async def list_available_mailboxes():
    """List available mailboxes from connected mail server"""
    try:
        # This will be implemented when mail server integration is ready
        # For now, return a placeholder response
        return {
            "mailboxes": [
                {"name": "INBOX", "full_name": "INBOX", "message_count": 0},
                {"name": "Sent", "full_name": "INBOX.Sent", "message_count": 0},
                {"name": "Drafts", "full_name": "INBOX.Drafts", "message_count": 0},
                {"name": "Spam", "full_name": "INBOX.Spam", "message_count": 0}
            ],
            "connected": False,
            "message": "Mail server integration not yet configured"
        }
    except Exception as e:
        logger.error(f"Error listing mailboxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for webhook execution
async def execute_webhook_delivery(webhook: dict, payload: dict, is_test: bool = False) -> dict:
    """Execute webhook delivery with retry logic and post-processing"""
    import time
    import aiohttp
    import asyncio
    
    webhook_id = str(webhook['_id'])
    execution_start = time.time()
    
    try:
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if webhook.get('api_key'):
            headers['Authorization'] = f"Bearer {webhook['api_key']}"
        
        # Execute webhook with timeout and retry logic
        max_retries = 3 if not is_test else 1
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        webhook['url'], 
                        json=payload, 
                        headers=headers
                    ) as response:
                        response_time = time.time() - execution_start
                        response_text = await response.text()
                        
                        # Log execution
                        await log_webhook_execution(
                            webhook_id=webhook_id,
                            status='success' if response.status < 400 else 'failed',
                            status_code=response.status,
                            response_time=response_time,
                            error_message=None if response.status < 400 else response_text[:500],
                            is_test=is_test
                        )
                        
                        if response.status < 400:
                            # Success - apply post-processing actions if not a test
                            if not is_test:
                                await apply_post_processing_actions(webhook, payload)
                            
                            return {
                                'success': True,
                                'status_code': response.status,
                                'response_time': response_time,
                                'response_body': response_text[:500]
                            }
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=response_text
                            )
                            
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    response_time = time.time() - execution_start
                    await log_webhook_execution(
                        webhook_id=webhook_id,
                        status='failed',
                        status_code=0,
                        response_time=response_time,
                        error_message=str(e)[:500],
                        is_test=is_test
                    )
                    
                    return {
                        'success': False,
                        'status_code': 0,
                        'response_time': response_time,
                        'error': str(e)
                    }
                else:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    
    except Exception as e:
        logger.error(f"Webhook execution error: {e}")
        return {
            'success': False,
            'status_code': 0,
            'response_time': 0,
            'error': str(e)
        }

async def log_webhook_execution(webhook_id: str, status: str, status_code: int, 
                               response_time: float, error_message: str = None, 
                               processed_message_id: str = None, mailbox: str = None,
                               is_test: bool = False):
    """Log webhook execution details"""
    try:
        logs_coll = get_collection('logs')
        
        log_entry = {
            'webhook_id': webhook_id,
            'timestamp': datetime.now(timezone.utc),
            'status': status,
            'status_code': status_code,
            'response_time': response_time,
            'error_message': error_message,
            'processed_message_id': processed_message_id,
            'mailbox': mailbox,
            'is_test': is_test
        }
        
        logs_coll.insert_one(log_entry)
        
        # Update webhook last execution info
        webhooks_coll = get_collection('webhooks')
        update_data = {
            'last_triggered': datetime.now(timezone.utc),
            'last_execution_status': status,
            '$inc': {'execution_count': 1}
        }
        
        webhooks_coll.update_one(
            {"_id": ObjectId(webhook_id)}, 
            {"$set": update_data}
        )
        
    except Exception as e:
        logger.error(f"Error logging webhook execution: {e}")

async def apply_post_processing_actions(webhook: dict, payload: dict):
    """Apply post-processing actions like mark as read, delete, etc."""
    try:
        post_actions = webhook.get('post_actions', {})
        actions_applied = {}
        
        # This will be implemented with IMAP integration
        # For now, just log what actions would be applied
        
        if post_actions.get('mark_as_read'):
            logger.info(f"Would mark message as read for webhook {webhook['_id']}")
            actions_applied['mark_as_read'] = True
            
        if post_actions.get('delete_message'):
            logger.info(f"Would delete message for webhook {webhook['_id']}")
            actions_applied['delete_message'] = True
            
        if post_actions.get('move_to_folder'):
            folder = post_actions['move_to_folder']
            logger.info(f"Would move message to folder '{folder}' for webhook {webhook['_id']}")
            actions_applied['move_to_folder'] = folder
              if post_actions.get('add_flag'):
            flag = post_actions['add_flag']
            logger.info(f"Would add flag '{flag}' to message for webhook {webhook['_id']}")
            actions_applied['add_flag'] = flag
            
        return actions_applied
        
    except Exception as e:
        logger.error(f"Error applying post-processing actions: {e}")
        return {}

# Mail Server Discovery and IMAP Integration Endpoints

@app.get("/api/mail-servers", response_model=List[Dict])
async def get_mail_servers():
    """Discover available NS8 mail servers"""
    try:
        discovery = MailServerDiscovery()
        servers = discovery.discover_mail_servers()
        return servers
    except Exception as e:
        logger.error(f"Error discovering mail servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mail-servers/{server_uuid}/mailboxes")
async def get_mailboxes(server_uuid: str, username: str, password: str):
    """Get mailboxes for a specific mail server"""
    try:
        # Get server info
        discovery = MailServerDiscovery()
        server = discovery.get_mail_server_by_uuid(server_uuid)
        if not server:
            raise HTTPException(status_code=404, detail="Mail server not found")
        
        # Connect to IMAP
        imap_client = IMAPClient(
            host=server['host'],
            port=server['imap_port'],
            use_ssl=server['imap_port'] == 993
        )
        
        if not imap_client.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to mail server")
        
        if not imap_client.login(username, password):
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Get mailboxes
        mailboxes = imap_client.list_mailboxes()
        imap_client.disconnect()
        
        # Convert to dict format
        mailbox_list = []
        for mailbox in mailboxes:
            mailbox_list.append({
                'name': mailbox.name,
                'flags': mailbox.flags,
                'delimiter': mailbox.delimiter,
                'exists': mailbox.exists,
                'unseen': mailbox.unseen
            })
        
        return mailbox_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mailboxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mail-servers/{server_uuid}/test-connection")
async def test_mail_server_connection(server_uuid: str, username: str, password: str):
    """Test connection to a mail server"""
    try:
        # Get server info
        discovery = MailServerDiscovery()
        server = discovery.get_mail_server_by_uuid(server_uuid)
        if not server:
            raise HTTPException(status_code=404, detail="Mail server not found")
        
        # Test connection
        imap_client = IMAPClient(
            host=server['host'],
            port=server['imap_port'],
            use_ssl=server['imap_port'] == 993
        )
        
        start_time = time.time()
        
        if not imap_client.connect():
            return {
                'success': False,
                'error': 'Failed to connect to mail server',
                'response_time': time.time() - start_time
            }
        
        if not imap_client.login(username, password):
            imap_client.disconnect()
            return {
                'success': False,
                'error': 'Authentication failed',
                'response_time': time.time() - start_time
            }
        
        # Test selecting INBOX
        mailbox_info = imap_client.select_mailbox('INBOX')
        imap_client.disconnect()
        
        response_time = time.time() - start_time
        
        return {
            'success': True,
            'response_time': response_time,
            'server_info': server,
            'mailbox_info': {
                'name': mailbox_info.name if mailbox_info else None,
                'exists': mailbox_info.exists if mailbox_info else False,
                'unseen': mailbox_info.unseen if mailbox_info else 0
            } if mailbox_info else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing mail server connection: {e}")
        return {
            'success': False,
            'error': str(e),
            'response_time': time.time() - start_time if 'start_time' in locals() else 0
        }

@app.get("/api/monitor/status")
async def get_monitor_status():
    """Get current status of the mail monitoring service"""
    try:
        status = get_monitor_status()
        return status
    except Exception as e:
        logger.error(f"Error getting monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitor/start")
async def start_monitor():
    """Start the mail monitoring service"""
    try:
        if not current_settings or not current_settings.get('mongodb_url'):
            raise HTTPException(status_code=400, detail="MongoDB URL not configured in settings")
        
        start_mail_monitor(current_settings['mongodb_url'])
        return {'message': 'Mail monitor started successfully'}
        
    except Exception as e:
        logger.error(f"Error starting mail monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitor/stop")
async def stop_monitor():
    """Stop the mail monitoring service"""
    try:
        stop_mail_monitor()
        return {'message': 'Mail monitor stopped successfully'}
        
    except Exception as e:
        logger.error(f"Error stopping mail monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced lifecycle management with mail monitor
@asynccontextmanager
async def enhanced_lifespan(app: FastAPI):
    # Startup
    mongodb_url = os.getenv('MONGODB_URL')
    if mongodb_url:
        connect_to_mongodb(mongodb_url)
        load_current_settings()
        
        # Auto-start mail monitor if configured
        if current_settings and current_settings.get('mongodb_url'):
            try:
                start_mail_monitor(current_settings['mongodb_url'])
                logger.info("Mail monitor auto-started")
            except Exception as e:
                logger.error(f"Failed to auto-start mail monitor: {e}")
    else:
        try:
            if connect_to_mongodb():
                logger.info("Mail Webhooks API started successfully")
            else:
                logger.warning("Started without MongoDB connection - configure via settings")
        except Exception as e:
            logger.warning(f"Started without MongoDB connection: {e}")
    
    yield
    
    # Shutdown
    try:
        stop_mail_monitor()
        logger.info("Mail monitor stopped during shutdown")
    except Exception as e:
        logger.error(f"Error stopping mail monitor during shutdown: {e}")
    
    if mongodb_client:
        mongodb_client.close()
    logger.info("Mail Webhooks API stopped")
app = FastAPI(
    title="Mail Webhooks API",
    description="API for managing mail webhooks with configurable MongoDB connection",
    version="1.0.0",
    lifespan=lifespan
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
