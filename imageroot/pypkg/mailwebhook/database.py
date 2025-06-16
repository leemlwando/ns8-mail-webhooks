"""
Database models and connection handling for ns8-mail-webhooks

Author: Lee M. Lwando <leemlwando@gmail.com>
Repository: https://github.com/leemlwando/ns8-mail-webhooks
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////var/lib/nethserver/mail-webhooks/schedules.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Schedule(Base):
    """Model for scheduled webhook triggers"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_to_monitor = Column(String, unique=True, index=True, nullable=False)
    webhook_url = Column(String, nullable=False)
    api_key = Column(String, nullable=True)
    payload_format = Column(String, default="RAW")  # RAW or JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessingLog(Base):
    """Model for tracking email processing history"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, nullable=True)  # NULL for one-time jobs
    mailbox = Column(String, nullable=False)
    email_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    webhook_url = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # "scheduled" or "onetime"
    status = Column(String, nullable=False)  # "success", "partial", "failed"
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database and create tables"""
    db_path = DATABASE_URL.split("///")[1] if "///" in DATABASE_URL else None
    if db_path:
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
