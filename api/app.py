"""
FastAPI server for NS8 Mail Webhooks
"""

import logging
import asyncio
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore

from .models import (
    WebhookCreate, WebhookUpdate, WebhookResponse, WebhookListResponse,
    WebhookStats, LogEntry, PaginationParams, EmailData
)
from .crud import WebhookCRUD, JobCRUD, LogCRUD
from .database import init_database, get_database, get_mongodb_url
from .email_handler import IMAPHandler, EmailProcessor
from .scheduler import SchedulerManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None
imap_handler: Optional[IMAPHandler] = None
scheduler_manager: Optional[SchedulerManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("Starting NS8 Mail Webhooks API...")
    
    # Initialize database
    await init_database()
    
    # Initialize scheduler
    global scheduler, imap_handler, scheduler_manager
    
    # Create MongoDB job store for APScheduler
    db_url = get_mongodb_url()
    jobstore = MongoDBJobStore(host=db_url)
    
    scheduler = AsyncIOScheduler(
        jobstores={'default': jobstore},
        timezone='UTC'
    )
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(scheduler)
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    # Initialize IMAP handler for real-time triggers
    imap_handler = IMAPHandler()
    
    # Load existing webhooks and set up their schedules
    webhooks = await WebhookCRUD.list_webhooks(PaginationParams(page=1, size=1000))
    for webhook in webhooks.webhooks:
        if webhook.enabled:
            if webhook.trigger_type == "scheduled" and webhook.schedule_interval:
                await scheduler_manager.schedule_webhook(webhook.id, webhook.schedule_interval)
            elif webhook.trigger_type == "real time":
                await imap_handler.add_email_monitor(webhook.email_address, webhook.id)
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NS8 Mail Webhooks API...")
    
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    if imap_handler:
        await imap_handler.close()
        logger.info("IMAP handler stopped")


app = FastAPI(
    title="NS8 Mail Webhooks API",
    description="API for managing email webhooks and scheduled jobs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to actual frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ns8-mail-webhooks"}


# Webhook endpoints
@app.post("/api/webhooks", response_model=WebhookResponse)
async def create_webhook(webhook: WebhookCreate, background_tasks: BackgroundTasks):
    """Create a new webhook"""
    try:
        # Create webhook in database
        created_webhook = await WebhookCRUD.create_webhook(webhook)
        
        # Set up scheduling/monitoring in background
        background_tasks.add_task(setup_webhook_triggers, created_webhook)
        
        return created_webhook
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status")
):
    """List webhooks with pagination and filtering"""
    try:
        params = PaginationParams(page=page, size=size)
        return await WebhookCRUD.list_webhooks(params, search, status, enabled)
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str):
    """Get a specific webhook by ID"""
    try:
        webhook = await WebhookCRUD.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: str, webhook_update: WebhookUpdate, background_tasks: BackgroundTasks):
    """Update a webhook"""
    try:
        # Check if webhook exists
        existing_webhook = await WebhookCRUD.get_webhook(webhook_id)
        if not existing_webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Update webhook
        updated_webhook = await WebhookCRUD.update_webhook(webhook_id, webhook_update)
        if not updated_webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Update scheduling/monitoring in background
        background_tasks.add_task(update_webhook_triggers, existing_webhook, updated_webhook)
        
        return updated_webhook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, background_tasks: BackgroundTasks):
    """Delete a webhook"""
    try:
        # Get webhook before deletion
        webhook = await WebhookCRUD.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Delete webhook
        success = await WebhookCRUD.delete_webhook(webhook_id)
        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Clean up scheduling/monitoring in background
        background_tasks.add_task(cleanup_webhook_triggers, webhook)
        
        return {"message": "Webhook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: str, background_tasks: BackgroundTasks):
    """Toggle webhook enabled/disabled status"""
    try:
        webhook = await WebhookCRUD.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Toggle enabled status
        update_data = WebhookUpdate(enabled=not webhook.enabled)
        updated_webhook = await WebhookCRUD.update_webhook(webhook_id, update_data)
        
        # Update triggers
        background_tasks.add_task(update_webhook_triggers, webhook, updated_webhook)
        
        return updated_webhook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str):
    """Test a webhook by sending a test payload"""
    try:
        webhook = await WebhookCRUD.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Create test email data
        test_email = EmailData(
            message_id="test-" + webhook_id,
            subject="Test Email",
            sender="test@example.com",
            recipients=[webhook.email_address],
            body="This is a test email for webhook testing.",
            headers={"X-Test": "true"},
            timestamp=datetime.utcnow(),
            webhook_id=webhook_id
        )
        
        # Process test email
        processor = EmailProcessor()
        result = await processor.process_email(test_email, webhook)
        
        return {"message": "Test webhook sent", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Job endpoints
@app.get("/api/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    webhook_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List jobs with pagination and filtering"""
    try:
        params = PaginationParams(page=page, size=size)
        return await JobCRUD.list_jobs(params, webhook_id, status)
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a specific job by ID"""
    try:
        job = await JobCRUD.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Log endpoints
@app.get("/api/logs")
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    webhook_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None)
):
    """List logs with pagination and filtering"""
    try:
        params = PaginationParams(page=page, size=size)
        return await LogCRUD.list_logs(params, webhook_id, level)
    except Exception as e:
        logger.error(f"Error listing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoint
@app.get("/api/stats", response_model=WebhookStats)
async def get_stats():
    """Get webhook statistics"""
    try:
        return await WebhookCRUD.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def setup_webhook_triggers(webhook: WebhookResponse):
    """Set up triggers for a new webhook"""
    try:
        if not webhook.enabled:
            return
            
        if webhook.trigger_type == "scheduled" and webhook.schedule_interval:
            if scheduler_manager:
                await scheduler_manager.schedule_webhook(webhook.id, webhook.schedule_interval)
        elif webhook.trigger_type == "real time":
            if imap_handler:
                await imap_handler.add_email_monitor(webhook.email_address, webhook.id)
                
        logger.info(f"Set up triggers for webhook {webhook.id}")
    except Exception as e:
        logger.error(f"Error setting up triggers for webhook {webhook.id}: {e}")


async def update_webhook_triggers(old_webhook: WebhookResponse, new_webhook: WebhookResponse):
    """Update triggers when webhook is modified"""
    try:
        # Remove old triggers
        await cleanup_webhook_triggers(old_webhook)
        
        # Set up new triggers
        await setup_webhook_triggers(new_webhook)
        
        logger.info(f"Updated triggers for webhook {new_webhook.id}")
    except Exception as e:
        logger.error(f"Error updating triggers for webhook {new_webhook.id}: {e}")


async def cleanup_webhook_triggers(webhook: WebhookResponse):
    """Clean up triggers when webhook is deleted or disabled"""
    try:
        if webhook.trigger_type == "scheduled" and scheduler_manager:
            await scheduler_manager.unschedule_webhook(webhook.id)
        elif webhook.trigger_type == "real time" and imap_handler:
            await imap_handler.remove_email_monitor(webhook.email_address, webhook.id)
            
        logger.info(f"Cleaned up triggers for webhook {webhook.id}")
    except Exception as e:
        logger.error(f"Error cleaning up triggers for webhook {webhook.id}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)