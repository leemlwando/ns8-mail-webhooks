"""
Pydantic models for webhook management
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class WebhookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    api_key: Optional[str] = None
    email_address: EmailStr
    payload_type: Literal["json", "raw"] = "json"
    post_action: Literal["none", "mark as read", "delete"] = "none"
    trigger_type: Literal["real time", "scheduled"] = "real time"
    schedule_interval: Optional[str] = None
    enabled: bool = True

    class Config:
        json_encoders = {ObjectId: str}


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    email_address: Optional[EmailStr] = None
    payload_type: Optional[Literal["json", "raw"]] = None
    post_action: Optional[Literal["none", "mark as read", "delete"]] = None
    trigger_type: Optional[Literal["real time", "scheduled"]] = None
    schedule_interval: Optional[str] = None
    enabled: Optional[bool] = None

    class Config:
        json_encoders = {ObjectId: str}


class Webhook(WebhookBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: Literal["active", "paused", "error"] = "active"
    error_message: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    api_key: Optional[str] = None
    email_address: str
    payload_type: str
    post_action: str
    trigger_type: str
    schedule_interval: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None


class JobBase(BaseModel):
    webhook_id: str
    job_type: Literal["webhook_trigger", "email_check"] = "webhook_trigger"
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class Job(JobBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class LogEntry(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    webhook_id: str
    job_id: Optional[str] = None
    level: Literal["info", "warning", "error", "debug"] = "info"
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class EmailData(BaseModel):
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    body: str
    headers: dict
    timestamp: datetime
    webhook_id: Optional[str] = None
    processed: bool = False


class WebhookStats(BaseModel):
    total_webhooks: int
    active_webhooks: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution: Optional[datetime] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class WebhookListResponse(BaseModel):
    webhooks: List[WebhookResponse]
    total: int
    page: int
    size: int
    pages: int
