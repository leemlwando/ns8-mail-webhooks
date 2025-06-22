"""
Scheduler management for webhook jobs
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .models import EmailData, WebhookResponse
from .crud import WebhookCRUD, JobCRUD, LogCRUD
from .email_handler import EmailProcessor

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manage scheduled webhook jobs"""
    
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.processor = EmailProcessor()
    
    async def schedule_webhook(self, webhook_id: str, schedule_interval: str):
        """Schedule a webhook to run on the specified interval"""
        try:
            job_id = f"webhook_{webhook_id}"
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Parse schedule interval and create trigger
            trigger = self._parse_schedule(schedule_interval)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_scheduled_webhook,
                trigger=trigger,
                args=[webhook_id],
                id=job_id,
                name=f"Webhook {webhook_id}",
                replace_existing=True
            )
            
            logger.info(f"Scheduled webhook {webhook_id} with interval {schedule_interval}")
            
        except Exception as e:
            logger.error(f"Error scheduling webhook {webhook_id}: {e}")
            raise
    
    async def unschedule_webhook(self, webhook_id: str):
        """Remove a webhook from the scheduler"""
        try:
            job_id = f"webhook_{webhook_id}"
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Unscheduled webhook {webhook_id}")
            
        except Exception as e:
            logger.error(f"Error unscheduling webhook {webhook_id}: {e}")
    
    def _parse_schedule(self, schedule_interval: str):
        """Parse schedule interval string into APScheduler trigger"""
        try:
            # Parse common interval formats
            if schedule_interval.startswith("every "):
                # Handle "every X minutes/hours/days" format
                parts = schedule_interval.split()
                if len(parts) >= 3:
                    value = int(parts[1])
                    unit = parts[2].rstrip('s')  # Remove plural 's'
                    
                    if unit in ['minute', 'minutes']:
                        return IntervalTrigger(minutes=value)
                    elif unit in ['hour', 'hours']:
                        return IntervalTrigger(hours=value)
                    elif unit in ['day', 'days']:
                        return IntervalTrigger(days=value)
            
            elif "/" in schedule_interval:
                # Handle cron-like format
                return CronTrigger.from_crontab(schedule_interval)
            
            elif schedule_interval in ["hourly", "daily", "weekly"]:
                # Handle predefined intervals
                if schedule_interval == "hourly":
                    return IntervalTrigger(hours=1)
                elif schedule_interval == "daily":
                    return IntervalTrigger(days=1)
                elif schedule_interval == "weekly":
                    return IntervalTrigger(weeks=1)
            
            # Default to hourly if parsing fails
            logger.warning(f"Could not parse schedule '{schedule_interval}', defaulting to hourly")
            return IntervalTrigger(hours=1)
            
        except Exception as e:
            logger.error(f"Error parsing schedule '{schedule_interval}': {e}")
            return IntervalTrigger(hours=1)
    
    async def _execute_scheduled_webhook(self, webhook_id: str):
        """Execute a scheduled webhook"""
        try:
            # Get webhook details
            webhook = await WebhookCRUD.get_webhook(webhook_id)
            if not webhook or not webhook.enabled:
                logger.warning(f"Webhook {webhook_id} not found or disabled, skipping execution")
                return
            
            # Create job record
            job = await JobCRUD.create_job(
                webhook_id=webhook_id,
                job_type="webhook_trigger",
                scheduled_at=datetime.utcnow()
            )
            
            try:
                # Mark job as running
                await JobCRUD.update_job_status(job.id, "running", started_at=datetime.utcnow())
                
                # Create mock email data for scheduled execution
                # In a real implementation, this might fetch actual emails
                # or use a different trigger mechanism
                email_data = EmailData(
                    message_id=f"scheduled_{webhook_id}_{datetime.utcnow().timestamp()}",
                    subject=f"Scheduled webhook execution - {webhook.name}",
                    sender="scheduler@ns8-mail-webhooks",
                    recipients=[webhook.email_address],
                    body="This is a scheduled webhook execution.",
                    headers={"X-Scheduled": "true"},
                    timestamp=datetime.utcnow(),
                    webhook_id=webhook_id
                )
                
                # Process the webhook
                result = await self.processor.process_email(email_data, webhook)
                
                # Update job status
                await JobCRUD.update_job_status(
                    job.id,
                    "completed" if result["success"] else "failed",
                    completed_at=datetime.utcnow(),
                    error_message=result.get("error") if not result["success"] else None
                )
                
                # Update webhook last run time
                await WebhookCRUD.update_last_run(webhook_id, datetime.utcnow())
                
                logger.info(f"Executed scheduled webhook {webhook_id}: {'success' if result['success'] else 'failed'}")
                
            except Exception as e:
                # Mark job as failed
                await JobCRUD.update_job_status(
                    job.id,
                    "failed",
                    completed_at=datetime.utcnow(),
                    error_message=str(e)
                )
                
                # Log error
                await LogCRUD.create_log(
                    webhook_id=webhook_id,
                    level="error",
                    message=f"Scheduled execution failed: {str(e)}",
                    details={"job_id": job.id, "error": str(e)}
                )
                
                logger.error(f"Error executing scheduled webhook {webhook_id}: {e}")
                
        except Exception as e:
            logger.error(f"Critical error in scheduled webhook execution {webhook_id}: {e}")
    
    def list_scheduled_jobs(self):
        """List all scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def get_job_status(self, webhook_id: str):
        """Get status of a scheduled job"""
        job_id = f"webhook_{webhook_id}"
        job = self.scheduler.get_job(job_id)
        
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            }
        return None
