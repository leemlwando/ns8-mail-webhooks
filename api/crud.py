"""
CRUD ofrom .models import (
    Webhook, WebhookCreate, WebhookUpdate, WebhookResponse,
    Job, JobBase, LogEntry, PaginationParams, WebhookListResponse,
    WebhookStats
)tions for webhooks, jobs, and logs
"""

import logging
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import (
    Webhook, WebhookCreate, WebhookUpdate, WebhookResponse,
    Job, JobBase, LogEntry, PaginationParams, WebhookListResponse, WebhookStats
)
from .database import get_database, get_collection_name

logger = logging.getLogger(__name__)


class WebhookCRUD:
    
    @staticmethod
    async def create_webhook(webhook_data: WebhookCreate) -> WebhookResponse:
        """Create a new webhook"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            webhook = Webhook(**webhook_data.dict())
            result = await collection.insert_one(webhook.dict(by_alias=True))
            
            # Get the created webhook
            created_webhook = await collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created webhook: {webhook.name} ({result.inserted_id})")
            return WebhookResponse(**created_webhook)
            
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise
    
    @staticmethod
    async def get_webhook(webhook_id: str) -> Optional[WebhookResponse]:
        """Get a webhook by ID"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            webhook = await collection.find_one({"_id": ObjectId(webhook_id)})
            if webhook:
                return WebhookResponse(**webhook)
            return None
            
        except Exception as e:
            logger.error(f"Error getting webhook {webhook_id}: {e}")
            raise
    
    @staticmethod
    async def get_webhooks(
        page: int = 1, 
        size: int = 10,
        enabled: Optional[bool] = None,
        trigger_type: Optional[str] = None
    ) -> WebhookListResponse:
        """Get paginated list of webhooks"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            # Build filter
            filter_dict = {}
            if enabled is not None:
                filter_dict["enabled"] = enabled
            if trigger_type:
                filter_dict["trigger_type"] = trigger_type
            
            # Get total count
            total = await collection.count_documents(filter_dict)
            
            # Calculate pagination
            skip = (page - 1) * size
            pages = (total + size - 1) // size
            
            # Get webhooks
            cursor = collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(size)
            webhooks_data = await cursor.to_list(length=size)
            
            webhooks = [WebhookResponse(**webhook) for webhook in webhooks_data]
            
            return WebhookListResponse(
                webhooks=webhooks,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting webhooks: {e}")
            raise
    
    @staticmethod
    async def list_webhooks(
        params: PaginationParams, 
        search: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> WebhookListResponse:
        """List webhooks with pagination and filtering"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            # Build filter
            filter_dict = {}
            if search:
                filter_dict["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"email_address": {"$regex": search, "$options": "i"}},
                    {"url": {"$regex": search, "$options": "i"}}
                ]
            if status:
                filter_dict["status"] = status
            if enabled is not None:
                filter_dict["enabled"] = enabled
            
            # Get total count
            total = await collection.count_documents(filter_dict)
            
            # Get paginated results
            skip = (params.page - 1) * params.size
            cursor = collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(params.size)
            webhooks_data = await cursor.to_list(length=params.size)
            
            webhooks = [WebhookResponse(**webhook) for webhook in webhooks_data]
            
            return WebhookListResponse(
                webhooks=webhooks,
                total=total,
                page=params.page,
                size=params.size,
                pages=(total + params.size - 1) // params.size
            )
            
        except Exception as e:
            logger.error(f"Error listing webhooks: {e}")
            raise
    
    @staticmethod
    async def update_webhook(webhook_id: str, webhook_update: WebhookUpdate) -> Optional[WebhookResponse]:
        """Update a webhook"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            # Build update data
            update_data = {k: v for k, v in webhook_update.dict(exclude_unset=True).items() if v is not None}
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
            
            # Update webhook
            result = await collection.update_one(
                {"_id": ObjectId(webhook_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            # Get updated webhook
            updated_webhook = await collection.find_one({"_id": ObjectId(webhook_id)})
            if updated_webhook:
                logger.info(f"Updated webhook: {webhook_id}")
                return WebhookResponse(**updated_webhook)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating webhook {webhook_id}: {e}")
            raise
    
    @staticmethod
    async def delete_webhook(webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            result = await collection.delete_one({"_id": ObjectId(webhook_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted webhook: {webhook_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting webhook {webhook_id}: {e}")
            raise
    
    @staticmethod
    async def get_enabled_webhooks() -> List[WebhookResponse]:
        """Get all enabled webhooks"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            cursor = collection.find({"enabled": True})
            webhooks_data = await cursor.to_list(length=None)
            
            return [WebhookResponse(**webhook) for webhook in webhooks_data]
            
        except Exception as e:
            logger.error(f"Error getting enabled webhooks: {e}")
            raise
    
    @staticmethod
    async def update_webhook_status(webhook_id: str, status: str, error_message: Optional[str] = None):
        """Update webhook status"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            elif status != "error":
                update_data["error_message"] = None
            
            await collection.update_one(
                {"_id": ObjectId(webhook_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating webhook status {webhook_id}: {e}")
            raise
    
    @staticmethod
    async def update_webhook_execution(webhook_id: str, last_run: datetime, next_run: Optional[datetime] = None):
        """Update webhook execution times"""
        try:
            db = await get_database()
            collection = db[get_collection_name("webhooks")]
            
            update_data = {
                "last_run": last_run,
                "updated_at": datetime.utcnow()
            }
            
            if next_run:
                update_data["next_run"] = next_run
            
            await collection.update_one(
                {"_id": ObjectId(webhook_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating webhook execution {webhook_id}: {e}")
            raise
    
    @staticmethod
    async def get_stats() -> WebhookStats:
        """Get webhook statistics"""
        try:
            db = await get_database()
            webhook_collection = db[get_collection_name("webhooks")]
            job_collection = db[get_collection_name("jobs")]
            
            # Get webhook counts
            total_webhooks = await webhook_collection.count_documents({})
            active_webhooks = await webhook_collection.count_documents({"enabled": True, "status": "active"})
            
            # Get job stats
            total_executions = await job_collection.count_documents({})
            successful_executions = await job_collection.count_documents({"status": "completed"})
            failed_executions = await job_collection.count_documents({"status": "failed"})
            
            # Get last execution
            last_job = await job_collection.find_one({}, sort=[("completed_at", -1)])
            last_execution = last_job.get("completed_at") if last_job else None
            
            return WebhookStats(
                total_webhooks=total_webhooks,
                active_webhooks=active_webhooks,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                last_execution=last_execution
            )
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise


class JobCRUD:
    
    @staticmethod
    async def create_job(job_data: JobBase) -> Job:
        """Create a new job"""
        try:
            db = await get_database()
            collection = db[get_collection_name("jobs")]
            
            job = Job(**job_data.dict())
            result = await collection.insert_one(job.dict(by_alias=True))
            
            created_job = await collection.find_one({"_id": result.inserted_id})
            logger.info(f"Created job for webhook {job_data.webhook_id}")
            
            return Job(**created_job)
            
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise
    
    @staticmethod
    async def get_job(job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        try:
            db = await get_database()
            collection = db[get_collection_name("jobs")]
            
            job = await collection.find_one({"_id": ObjectId(job_id)})
            if job:
                return Job(**job)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            raise
    
    @staticmethod
    async def list_jobs(
        params: PaginationParams,
        webhook_id: Optional[str] = None,
        status: Optional[str] = None
    ):
        """List jobs with pagination and filtering"""
        try:
            db = await get_database()
            collection = db[get_collection_name("jobs")]
            
            # Build filter
            filter_dict = {}
            if webhook_id:
                filter_dict["webhook_id"] = webhook_id
            if status:
                filter_dict["status"] = status
            
            # Get total count
            total = await collection.count_documents(filter_dict)
            
            # Get paginated results
            skip = (params.page - 1) * params.size
            cursor = collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(params.size)
            jobs_data = await cursor.to_list(length=params.size)
            
            jobs = [Job(**job) for job in jobs_data]
            
            return {
                "jobs": jobs,
                "total": total,
                "page": params.page,
                "size": params.size,
                "pages": (total + params.size - 1) // params.size
            }
            
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            raise
    
    @staticmethod
    async def update_job_status(
        job_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update job status and timing"""
        try:
            db = await get_database()
            collection = db[get_collection_name("jobs")]
            
            update_data = {"status": status}
            if started_at:
                update_data["started_at"] = started_at
            if completed_at:
                update_data["completed_at"] = completed_at
            if error_message:
                update_data["error_message"] = error_message
            
            result = await collection.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_data}
            )
            
            return result.matched_count > 0
            
        except Exception as e:
            logger.error(f"Error updating job status {job_id}: {e}")
            raise


class LogCRUD:
    
    @staticmethod
    async def create_log(
        webhook_id: str,
        level: str = "info",
        message: str = "",
        details: Optional[dict] = None,
        job_id: Optional[str] = None
    ) -> LogEntry:
        """Create a new log entry"""
        try:
            db = await get_database()
            collection = db[get_collection_name("logs")]
            
            log_data = {
                "webhook_id": webhook_id,
                "level": level,
                "message": message,
                "details": details,
                "job_id": job_id
            }
            
            log = LogEntry(**log_data)
            await collection.insert_one(log.dict(by_alias=True))
            
            return log
            
        except Exception as e:
            logger.error(f"Error creating log: {e}")
            raise
    
    @staticmethod
    async def list_logs(
        params: PaginationParams,
        webhook_id: Optional[str] = None,
        level: Optional[str] = None
    ):
        """List logs with pagination and filtering"""
        try:
            db = await get_database()
            collection = db[get_collection_name("logs")]
            
            # Build filter
            filter_dict = {}
            if webhook_id:
                filter_dict["webhook_id"] = webhook_id
            if level:
                filter_dict["level"] = level
            
            # Get total count
            total = await collection.count_documents(filter_dict)
            
            # Get paginated results
            skip = (params.page - 1) * params.size
            cursor = collection.find(filter_dict).sort("timestamp", -1).skip(skip).limit(params.size)
            logs_data = await cursor.to_list(length=params.size)
            
            logs = [LogEntry(**log) for log in logs_data]
            
            return {
                "logs": logs,
                "total": total,
                "page": params.page,
                "size": params.size,
                "pages": (total + params.size - 1) // params.size
            }
            
        except Exception as e:
            logger.error(f"Error listing logs: {e}")
            raise
