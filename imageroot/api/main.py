#!/usr/bin/env python3
"""
Mail Webhooks API Server with NS8 Mail Monitor Integration
Starts both the FastAPI server and the mail monitoring service
"""

import os
import logging
import signal
import sys
import threading
import time
from contextlib import asynccontextmanager

import uvicorn

# Import our application components
from app import app, connect_to_mongodb
from mail_monitor import start_mail_monitor, stop_mail_monitor, get_monitor_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for service management
mail_monitor_started = False
shutdown_event = threading.Event()

def start_mail_monitoring_service():
    """Start the mail monitoring service"""
    global mail_monitor_started
    
    try:
        mongodb_url = os.getenv('MONGODB_URL')
        if not mongodb_url:
            logger.error("MONGODB_URL not configured - mail monitoring disabled")
            return
        
        settings = {
            'database_name': 'mail_webhooks',
            'webhooks_collection': os.getenv('WEBHOOKS_COLLECTION', 'webhooks'),
            'events_collection': os.getenv('EVENTS_COLLECTION', 'events'),
            'settings_collection': os.getenv('SETTINGS_COLLECTION', 'settings'),
            'triggers_collection': os.getenv('TRIGGERS_COLLECTION', 'triggers'),
            'logs_collection': os.getenv('LOGS_COLLECTION', 'logs'),
            'mail_server_uuid': os.getenv('MAIL_SERVER_UUID', '')
        }
        
        logger.info("Starting mail monitoring service with NS8 integration...")
        start_mail_monitor(mongodb_url, settings)
        mail_monitor_started = True
        logger.info("Mail monitoring service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start mail monitoring service: {e}")

def stop_services():
    """Stop all services gracefully"""
    global mail_monitor_started
    
    logger.info("Stopping services...")
    shutdown_event.set()
    
    if mail_monitor_started:
        try:
            stop_mail_monitor()
            mail_monitor_started = False
            logger.info("Mail monitoring service stopped")
        except Exception as e:
            logger.error(f"Error stopping mail monitor: {e}")
    
    logger.info("All services stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    stop_services()
    sys.exit(0)

@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager"""
    # Startup
    logger.info("Starting Mail Webhooks API server...")
    
    # Connect to MongoDB
    mongodb_url = os.getenv('MONGODB_URL')
    if mongodb_url:
        connect_to_mongodb(mongodb_url)
        logger.info("Connected to MongoDB")
    else:
        logger.warning("MONGODB_URL not configured")
    
    # Start mail monitoring service in background thread
    monitor_thread = threading.Thread(target=start_mail_monitoring_service)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Add health check endpoint for monitoring service
    @app.get("/api/monitor/status")
    async def monitor_status():
        return get_monitor_status()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mail Webhooks API server...")
    stop_services()

# Update app with lifespan
app.router.lifespan_context = lifespan

def main():
    """Main entry point"""
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting Mail Webhooks server with NS8 integration...")
        logger.info(f"Environment: MONGODB_URL={'***' if os.getenv('MONGODB_URL') else 'NOT SET'}")
        logger.info(f"Environment: MAIL_SERVER_UUID={os.getenv('MAIL_SERVER_UUID', 'NOT SET')}")
        
        # Start the FastAPI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8080,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        stop_services()

if __name__ == "__main__":
    main()
