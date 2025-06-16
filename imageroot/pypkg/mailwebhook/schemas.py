"""
Pydantic schemas for API request/response validation

Author: Lee M. Lwando <leemlwando@gmail.com>
Repository: https://github.com/leemlwando/ns8-mail-webhooks
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List
from datetime import datetime

class ScheduleBase(BaseModel):
    """Base schema for schedule operations"""
    mailbox_to_monitor: EmailStr
    webhook_url: HttpUrl
    api_key: Optional[str] = None
    payload_format: str = Field(default="RAW", pattern="^(RAW|JSON)$")
    is_active: bool = True

class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule"""
    pass

class ScheduleUpdate(ScheduleBase):
    """Schema for updating an existing schedule"""
    pass

class ScheduleResponse(ScheduleBase):
    """Schema for schedule responses"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OneTimeJob(BaseModel):
    """Schema for one-time job requests"""
    mailbox_to_process: EmailStr
    webhook_url: HttpUrl
    api_key: Optional[str] = None
    payload_format: str = Field(default="RAW", pattern="^(RAW|JSON)$")
    post_scrape_action: str = Field(default="mark_as_read", pattern="^(mark_as_read|delete)$")

class JobResult(BaseModel):
    """Schema for job execution results"""
    status: str
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0
    message: Optional[str] = None
    errors: Optional[List[str]] = None

class MailboxInfo(BaseModel):
    """Schema for mailbox information"""
    address: EmailStr
    display_name: Optional[str] = None
    quota_used: Optional[int] = None
    quota_limit: Optional[int] = None

class ProcessingLogResponse(BaseModel):
    """Schema for processing log responses"""
    id: int
    schedule_id: Optional[int]
    mailbox: str
    email_count: int
    success_count: int
    error_count: int
    webhook_url: str
    job_type: str
    status: str
    error_message: Optional[str]
    processed_at: datetime

    class Config:
        from_attributes = True
