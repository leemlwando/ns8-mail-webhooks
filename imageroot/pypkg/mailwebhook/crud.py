"""
CRUD operations for database management

Author: Lee M. Lwando <leemlwando@gmail.com>
Repository: https://github.com/leemlwando/ns8-mail-webhooks
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from . import database, schemas

def get_schedule(db: Session, schedule_id: int) -> Optional[database.Schedule]:
    """Get a schedule by ID"""
    return db.query(database.Schedule).filter(database.Schedule.id == schedule_id).first()

def get_schedules(db: Session, skip: int = 0, limit: int = 100) -> List[database.Schedule]:
    """Get all schedules with pagination"""
    return db.query(database.Schedule).offset(skip).limit(limit).all()

def get_active_schedules(db: Session) -> List[database.Schedule]:
    """Get all active schedules"""
    return db.query(database.Schedule).filter(database.Schedule.is_active == True).all()

def create_schedule(db: Session, schedule: schemas.ScheduleCreate) -> database.Schedule:
    """Create a new schedule"""
    db_schedule = database.Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def update_schedule(db: Session, schedule_id: int, schedule: schemas.ScheduleUpdate) -> Optional[database.Schedule]:
    """Update an existing schedule"""
    db_schedule = get_schedule(db, schedule_id)
    if db_schedule:
        update_data = schedule.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_schedule, key, value)
        db.commit()
        db.refresh(db_schedule)
    return db_schedule

def delete_schedule(db: Session, schedule_id: int) -> Optional[database.Schedule]:
    """Delete a schedule"""
    db_schedule = get_schedule(db, schedule_id)
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
    return db_schedule

def log_processing_result(
    db: Session,
    schedule_id: Optional[int],
    mailbox: str,
    webhook_url: str,
    job_type: str,
    result: Dict[str, Any]
) -> database.ProcessingLog:
    """Log the result of email processing"""
    error_message = None
    if result.get("errors"):
        error_message = "; ".join(result["errors"])
    
    log_entry = database.ProcessingLog(
        schedule_id=schedule_id,
        mailbox=mailbox,
        email_count=result.get("processed_count", 0),
        success_count=result.get("success_count", 0),
        error_count=result.get("error_count", 0),
        webhook_url=webhook_url,
        job_type=job_type,
        status=result.get("status", "unknown"),
        error_message=error_message
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def get_processing_logs(db: Session, skip: int = 0, limit: int = 50) -> List[database.ProcessingLog]:
    """Get processing logs with pagination"""
    return db.query(database.ProcessingLog).order_by(database.ProcessingLog.processed_at.desc()).offset(skip).limit(limit).all()
