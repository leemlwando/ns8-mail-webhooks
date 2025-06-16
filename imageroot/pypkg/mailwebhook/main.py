"""
Main FastAPI application for NethServer 8 Mail Webhooks module

This module provides email processing capabilities by connecting to mailboxes
via IMAP and forwarding email content to configured webhooks.

Author: Lee M. Lwando <leemlwando@gmail.com>
Repository: https://github.com/leemlwando/ns8-mail-webhooks
License: MIT

References:
- NethServer 8 Module Development: https://nethserver.github.io/ns8-core/modules/
- NethServer 8 API Standards: https://nethserver.github.io/ns8-core/modules/rootfull/
"""

import asyncio
import threading
import time
import schedule
import os
import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas, database, imap_client
from .version import __version__

# Configure logging per NethServer 8 standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
database.init_db()

# Create FastAPI app following NethServer 8 conventions
app = FastAPI(
    title="NethServer 8 Mail Webhooks",
    description="Email processing and webhook forwarding module for NethServer 8",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware for NethServer 8 UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scheduler control
scheduler_running = False
scheduler_thread = None

def run_scheduled_jobs():
    """Execute all active scheduled jobs"""
    logger.info("Running scheduled jobs...")
    db = next(database.get_db())
    
    try:
        active_schedules = crud.get_active_schedules(db)
        logger.info(f"Processing {len(active_schedules)} active schedules")
        
        processor = imap_client.IMAPProcessor()
        
        for schedule_obj in active_schedules:
            logger.info(f"Processing schedule for: {schedule_obj.mailbox_to_monitor}")
            
            # Get password from environment (following NethServer 8 security practices)
            env_var_name = f"MAILBOX_PASSWORD_{schedule_obj.mailbox_to_monitor.replace('@', '_').replace('.', '_')}"
            password = os.getenv(env_var_name)
            
            if not password:
                logger.warning(f"Password not found for {schedule_obj.mailbox_to_monitor}")
                continue
            
            try:
                result = processor.process_mailbox(
                    mailbox_user=schedule_obj.mailbox_to_monitor,
                    mailbox_password=password,
                    webhook_url=str(schedule_obj.webhook_url),
                    api_key=schedule_obj.api_key,
                    payload_format=schedule_obj.payload_format,
                    post_scrape_action="delete",  # For scheduled jobs, delete to avoid reprocessing
                    process_all=False  # Only process new emails
                )
                
                # Log the result
                crud.log_processing_result(
                    db=db,
                    schedule_id=schedule_obj.id,
                    mailbox=schedule_obj.mailbox_to_monitor,
                    webhook_url=str(schedule_obj.webhook_url),
                    job_type="scheduled",
                    result=result
                )
                
                logger.info(f"Processed {result['success_count']} emails for {schedule_obj.mailbox_to_monitor}")
                
            except Exception as e:
                logger.error(f"Error processing schedule {schedule_obj.id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in scheduled job execution: {e}")
    finally:
        db.close()

def run_scheduler():
    """Background scheduler thread"""
    global scheduler_running
    scheduler_running = True
    
    # Schedule job every minute (configurable via environment)
    interval = int(os.getenv("POLLING_INTERVAL", "60"))  # seconds
    schedule.every(interval).seconds.do(run_scheduled_jobs)
    
    logger.info(f"Scheduler started with {interval}s interval")
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup"""
    global scheduler_thread
    
    logger.info("Starting Mail Webhooks module...")
    
    # Start background scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Mail Webhooks module started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scheduler_running
    
    logger.info("Shutting down Mail Webhooks module...")
    scheduler_running = False
    
    if scheduler_thread:
        scheduler_thread.join(timeout=5)

# API Routes following NethServer 8 conventions

@app.get("/api/status")
async def get_status():
    """Health check endpoint required by NethServer 8"""
    return {
        "status": "healthy",
        "version": __version__,
        "scheduler_running": scheduler_running
    }

@app.post("/api/schedules/", response_model=schemas.ScheduleResponse, status_code=201)
async def create_schedule(
    schedule: schemas.ScheduleCreate, 
    db: Session = Depends(database.get_db)
):
    """Create a new scheduled webhook trigger"""
    try:
        return crud.create_schedule(db=db, schedule=schedule)
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/schedules/", response_model=List[schemas.ScheduleResponse])
async def list_schedules(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """List all scheduled webhook triggers"""
    return crud.get_schedules(db, skip=skip, limit=limit)

@app.put("/api/schedules/{schedule_id}", response_model=schemas.ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule: schemas.ScheduleUpdate,
    db: Session = Depends(database.get_db)
):
    """Update an existing scheduled webhook trigger"""
    db_schedule = crud.update_schedule(db=db, schedule_id=schedule_id, schedule=schedule)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@app.delete("/api/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int, 
    db: Session = Depends(database.get_db)
):
    """Delete a scheduled webhook trigger"""
    db_schedule = crud.delete_schedule(db=db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

@app.post("/api/actions/run-now", response_model=schemas.JobResult)
async def run_one_time_job(
    job: schemas.OneTimeJob,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db)
):
    """Execute a one-time email processing job"""
    logger.info(f"Starting one-time job for: {job.mailbox_to_process}")
    
    # Get mailbox password
    env_var_name = f"MAILBOX_PASSWORD_{job.mailbox_to_process.replace('@', '_').replace('.', '_')}"
    password = os.getenv(env_var_name)
    
    if not password:
        raise HTTPException(
            status_code=400, 
            detail=f"Password not configured for mailbox {job.mailbox_to_process}"
        )
    
    try:
        processor = imap_client.IMAPProcessor()
        result = processor.process_mailbox(
            mailbox_user=job.mailbox_to_process,
            mailbox_password=password,
            webhook_url=str(job.webhook_url),
            api_key=job.api_key,
            payload_format=job.payload_format,
            post_scrape_action=job.post_scrape_action,
            process_all=True  # Process all emails for one-time jobs
        )
        
        # Log the result
        crud.log_processing_result(
            db=db,
            schedule_id=None,
            mailbox=job.mailbox_to_process,
            webhook_url=str(job.webhook_url),
            job_type="onetime",
            result=result
        )
        
        return schemas.JobResult(**result)
        
    except Exception as e:
        logger.error(f"Error in one-time job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/", response_model=List[schemas.ProcessingLogResponse])
async def get_processing_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db)
):
    """Get processing history logs"""
    return crud.get_processing_logs(db, skip=skip, limit=limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
