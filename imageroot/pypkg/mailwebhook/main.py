from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import os
import time

from .storage import WebhookStorage
from .processor import EmailProcessor
from .imap_client import SimpleIMAPClient

# Initialize FastAPI app
app = FastAPI(
    title="NethServer Mail Webhook Service",
    version="1.0.0",
    docs_url="/api/docs" if os.getenv("DEBUG") else None
)

# Add CORS middleware for development
if os.getenv("DEBUG"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Initialize components
storage = WebhookStorage()
processor = EmailProcessor()

# Pydantic models for API
class WebhookConfig(BaseModel):
    name: str
    mailbox: str
    webhook_url: str
    api_key: Optional[str] = None
    payload_format: str = "RAW"
    is_active: bool = True

class OneTimeJob(BaseModel):
    mailbox: str
    webhook_url: str
    api_key: Optional[str] = None
    payload_format: str = "RAW"
    post_scrape_action: str = "mark_as_read"

class WebhookTest(BaseModel):
    webhook_url: str
    api_key: Optional[str] = None

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for container health monitoring"""
    try:
        # Test database connection
        stats = storage.get_stats()
        
        return {
            "status": "healthy",
            "stats": stats,
            "database": "connected",
            "container_id": os.getenv("HOSTNAME", "unknown")
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e)
            }
        )

# Configuration endpoints
@app.get("/api/configs")
async def get_configs():
    """Get all webhook configurations"""
    try:
        configs = storage.get_configs()
        return {"configs": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs")
async def create_config(config: WebhookConfig):
    """Create or update webhook configuration"""
    try:
        config_id = storage.save_config(config.dict())
        return {"id": config_id, "message": "Configuration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/configs/{config_id}")
async def get_config(config_id: int):
    """Get a specific webhook configuration"""
    try:
        config = storage.get_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/configs/{config_id}")
async def delete_config(config_id: int):
    """Delete webhook configuration"""
    try:
        success = storage.delete_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return {"message": "Configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job endpoints
@app.post("/api/jobs/one-time")
async def run_one_time_job(job: OneTimeJob, background_tasks: BackgroundTasks):
    """Run a one-time email processing job"""
    try:
        config = job.dict()
        config['name'] = f"one-time-{int(time.time())}"
        
        # Run in background to avoid UI timeout
        background_tasks.add_task(processor.process_one_time_job, config)
        
        return {"message": "One-time job started successfully", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/test")
async def test_webhook(test_data: WebhookTest):
    """Test a webhook URL"""
    try:
        result = processor.test_webhook(test_data.webhook_url, test_data.api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Logging endpoints
@app.get("/api/logs")
async def get_logs(config_id: Optional[int] = None, limit: int = 100):
    """Get processing logs"""
    try:
        logs = storage.get_logs(config_id, limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get processing statistics"""
    try:
        stats = storage.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mailbox endpoints (for integration with ns8-mail)
@app.get("/api/mailboxes")
async def get_mailboxes():
    """Get available mailboxes from mail server"""
    try:
        imap_user = os.getenv('MAIL_ADMIN_USER')
        imap_pass = os.getenv('MAIL_ADMIN_PASS')
        
        if not imap_user or not imap_pass:
            return {"mailboxes": []}
        
        imap = SimpleIMAPClient()
        
        if imap.connect(imap_user, imap_pass):
            mailboxes = imap.list_mailboxes()
            imap.disconnect()
            
            # Format for frontend
            formatted_mailboxes = [
                {"address": mb, "name": mb} for mb in mailboxes
            ]
            return {"mailboxes": formatted_mailboxes}
        else:
            return {"mailboxes": []}
            
    except Exception as e:
        print(f"Error fetching mailboxes: {e}")
        return {"mailboxes": []}

# Static file serving for UI
@app.get("/")
async def serve_ui():
    """Serve the main UI"""
    return {"message": "Mail Webhook Service API", "version": "1.0.0"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for logging"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

def main():
    """Main entry point"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "mailwebhook.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("DEBUG") == "1"
    )

if __name__ == "__main__":
    main()
