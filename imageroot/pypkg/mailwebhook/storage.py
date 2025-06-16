import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

class WebhookStorage:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', '/var/lib/nethserver/mail-webhook/webhooks.db')
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrent access
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    mailbox TEXT NOT NULL,
                    webhook_url TEXT NOT NULL,
                    api_key TEXT,
                    payload_format TEXT DEFAULT 'RAW',
                    check_interval INTEGER DEFAULT 60,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER,
                    message_id TEXT,
                    subject TEXT,
                    status TEXT,
                    error_message TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES webhook_configs (id)
                )
            """)
            
            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_config_date 
                ON processing_logs(config_id, processed_at DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_status 
                ON processing_logs(status, processed_at DESC)
            """)
            
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_config(self, config: Dict) -> int:
        with self.get_connection() as conn:
            # Check if config with same name exists
            existing = conn.execute(
                "SELECT id FROM webhook_configs WHERE name = ?", 
                (config['name'],)
            ).fetchone()
            
            if existing:
                # Update existing
                cursor = conn.execute("""
                    UPDATE webhook_configs 
                    SET mailbox = ?, webhook_url = ?, api_key = ?, 
                        payload_format = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (
                    config['mailbox'], 
                    config['webhook_url'],
                    config.get('api_key'),
                    config.get('payload_format', 'RAW'),
                    config.get('is_active', True),
                    config['name']
                ))
                conn.commit()
                return existing['id']
            else:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO webhook_configs 
                    (name, mailbox, webhook_url, api_key, payload_format, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    config['name'],
                    config['mailbox'], 
                    config['webhook_url'],
                    config.get('api_key'),
                    config.get('payload_format', 'RAW'),
                    config.get('is_active', True)
                ))
                conn.commit()
                return cursor.lastrowid
    
    def get_configs(self, active_only: bool = False) -> List[Dict]:
        with self.get_connection() as conn:
            query = "SELECT * FROM webhook_configs"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_at DESC"
            
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]
    
    def get_config(self, config_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM webhook_configs WHERE id = ?", 
                (config_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def delete_config(self, config_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM webhook_configs WHERE id = ?", 
                (config_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def log_processing(self, config_id: int, message_id: str, subject: str, 
                      status: str, error_message: str = None):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO processing_logs 
                (config_id, message_id, subject, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (config_id, message_id, subject, status, error_message))
            conn.commit()
    
    def get_logs(self, config_id: int = None, limit: int = 100) -> List[Dict]:
        with self.get_connection() as conn:
            if config_id:
                query = """
                    SELECT l.*, c.name as config_name 
                    FROM processing_logs l 
                    JOIN webhook_configs c ON l.config_id = c.id
                    WHERE l.config_id = ? 
                    ORDER BY l.processed_at DESC 
                    LIMIT ?
                """
                rows = conn.execute(query, (config_id, limit)).fetchall()
            else:
                query = """
                    SELECT l.*, c.name as config_name 
                    FROM processing_logs l 
                    JOIN webhook_configs c ON l.config_id = c.id
                    ORDER BY l.processed_at DESC 
                    LIMIT ?
                """
                rows = conn.execute(query, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        with self.get_connection() as conn:
            # Get total configs
            total_configs = conn.execute(
                "SELECT COUNT(*) as count FROM webhook_configs"
            ).fetchone()['count']
            
            # Get active configs
            active_configs = conn.execute(
                "SELECT COUNT(*) as count FROM webhook_configs WHERE is_active = 1"
            ).fetchone()['count']
            
            # Get today's processing stats
            today_success = conn.execute("""
                SELECT COUNT(*) as count FROM processing_logs 
                WHERE status = 'SUCCESS' AND DATE(processed_at) = DATE('now')
            """).fetchone()['count']
            
            today_failed = conn.execute("""
                SELECT COUNT(*) as count FROM processing_logs 
                WHERE status IN ('FAILED', 'ERROR') AND DATE(processed_at) = DATE('now')
            """).fetchone()['count']
            
            return {
                'total_configs': total_configs,
                'active_configs': active_configs,
                'today_processed': today_success + today_failed,
                'today_success': today_success,
                'today_failed': today_failed,
                'success_rate': round((today_success / max(1, today_success + today_failed)) * 100, 2)
            }
