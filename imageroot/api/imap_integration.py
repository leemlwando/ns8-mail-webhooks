#!/usr/bin/env python3
"""
IMAP Integration Module
Handles IMAP connections, mailbox monitoring, and email processing for webhooks
"""

import imaplib
import email
import json
import logging
import time
import re
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
import ssl
import socket
import threading
import queue
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MailboxInfo:
    """Information about a mailbox"""
    name: str
    flags: List[str]
    delimiter: str
    exists: bool = True
    recent: int = 0
    unseen: int = 0

@dataclass
class EmailMessage:
    """Processed email message data"""
    id: str
    uid: str
    mailbox: str
    sender: str
    recipient: str
    subject: str
    timestamp: datetime
    size_bytes: int
    has_attachments: bool
    flags: List[str]
    headers: Dict[str, str]
    body_text: str
    body_html: str
    attachments: List[Dict[str, Any]]
    raw_message: Optional[bytes] = None

class IMAPClient:
    """Enhanced IMAP client for NS8 mail server integration"""
    
    def __init__(self, host: str, port: int = 143, use_ssl: bool = False, timeout: int = 30):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.imap = None
        self.connected = False
        self.authenticated = False
        self.current_mailbox = None
        
    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            if self.use_ssl or self.port == 993:
                # Create SSL context
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.imap = imaplib.IMAP4_SSL(self.host, self.port, ssl_context=context)
            else:
                self.imap = imaplib.IMAP4(self.host, self.port)
            
            self.imap.sock.settimeout(self.timeout)
            self.connected = True
            logger.info(f"Connected to IMAP server {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate with IMAP server"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            result, data = self.imap.login(username, password)
            if result == 'OK':
                self.authenticated = True
                logger.info(f"Successfully authenticated as {username}")
                return True
            else:
                logger.error(f"Authentication failed: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.authenticated = False
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        try:
            if self.imap and self.connected:
                if self.authenticated:
                    self.imap.logout()
                else:
                    self.imap.close()
            self.imap = None
            self.connected = False
            self.authenticated = False
            self.current_mailbox = None
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def list_mailboxes(self) -> List[MailboxInfo]:
        """List all available mailboxes"""
        if not self.authenticated:
            return []
        
        mailboxes = []
        try:
            result, data = self.imap.list()
            if result == 'OK':
                for line in data:
                    if line:
                        # Parse mailbox line: (flags) "delimiter" "name"
                        line_str = line.decode('utf-8')
                        match = re.match(r'\(([^)]*)\)\s+"([^"]*)"\s+"?([^"]*)"?', line_str)
                        if match:
                            flags = match.group(1).split()
                            delimiter = match.group(2)
                            name = match.group(3)
                            
                            mailbox = MailboxInfo(
                                name=name,
                                flags=flags,
                                delimiter=delimiter
                            )
                            mailboxes.append(mailbox)
                            
        except Exception as e:
            logger.error(f"Error listing mailboxes: {e}")
        
        return mailboxes
    
    def select_mailbox(self, mailbox: str = 'INBOX') -> Optional[MailboxInfo]:
        """Select a mailbox for operations"""
        if not self.authenticated:
            return None
        
        try:
            result, data = self.imap.select(mailbox)
            if result == 'OK':
                self.current_mailbox = mailbox
                # Get mailbox status
                exists = int(data[0]) if data and data[0] else 0
                
                # Get unseen count
                unseen = 0
                try:
                    result, data = self.imap.status(mailbox, '(UNSEEN)')
                    if result == 'OK' and data:
                        match = re.search(r'UNSEEN (\d+)', data[0].decode())
                        if match:
                            unseen = int(match.group(1))
                except:
                    pass
                
                return MailboxInfo(
                    name=mailbox,
                    flags=[],
                    delimiter='/',
                    exists=True,
                    recent=0,
                    unseen=unseen
                )
            else:
                logger.error(f"Failed to select mailbox {mailbox}: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error selecting mailbox {mailbox}: {e}")
            return None
    
    def search_messages(self, criteria: str = 'ALL') -> List[str]:
        """Search for messages matching criteria"""
        if not self.current_mailbox:
            return []
        
        try:
            result, data = self.imap.search(None, criteria)
            if result == 'OK':
                message_ids = data[0].decode().split() if data[0] else []
                return message_ids
            else:
                logger.error(f"Search failed: {data}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    def fetch_message(self, message_id: str, fetch_body: bool = True) -> Optional[EmailMessage]:
        """Fetch and parse a single message"""
        if not self.current_mailbox:
            return None
        
        try:
            # Fetch message data
            fetch_items = '(UID RFC822.SIZE FLAGS ENVELOPE'
            if fetch_body:
                fetch_items += ' RFC822'
            fetch_items += ')'
            
            result, data = self.imap.fetch(message_id, fetch_items)
            if result != 'OK' or not data:
                return None
            
            # Parse message data
            uid = None
            size = 0
            flags = []
            envelope = None
            raw_message = None
            
            for item in data:
                if isinstance(item, tuple):
                    if fetch_body and item[1]:
                        raw_message = item[1]
                    
                    # Parse response items
                    response = item[0].decode() if isinstance(item[0], bytes) else str(item[0])
                    
                    # Extract UID
                    uid_match = re.search(r'UID (\d+)', response)
                    if uid_match:
                        uid = uid_match.group(1)
                    
                    # Extract size
                    size_match = re.search(r'RFC822\.SIZE (\d+)', response)
                    if size_match:
                        size = int(size_match.group(1))
                    
                    # Extract flags
                    flags_match = re.search(r'FLAGS \(([^)]*)\)', response)
                    if flags_match:
                        flags = flags_match.group(1).split()
            
            if not raw_message:
                logger.warning(f"No message body fetched for message {message_id}")
                return None
            
            # Parse email content
            try:
                msg = email.message_from_bytes(raw_message)
            except Exception as e:
                logger.error(f"Failed to parse message {message_id}: {e}")
                return None
            
            # Extract basic information
            sender = parseaddr(msg.get('From', ''))[1] or msg.get('From', '')
            recipient = parseaddr(msg.get('To', ''))[1] or msg.get('To', '')
            subject = msg.get('Subject', '')
            date_str = msg.get('Date', '')
            
            # Parse date
            timestamp = datetime.now(timezone.utc)
            if date_str:
                try:
                    timestamp = email.utils.parsedate_to_datetime(date_str)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                except:
                    pass
            
            # Extract headers
            headers = {}
            for key, value in msg.items():
                headers[key] = value
            
            # Extract body and attachments
            body_text = ""
            body_html = ""
            attachments = []
            has_attachments = False
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('Content-Disposition', '')
                    
                    if 'attachment' in content_disposition:
                        has_attachments = True
                        filename = part.get_filename()
                        if filename:
                            attachments.append({
                                'filename': filename,
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
                    elif content_type == 'text/plain' and 'attachment' not in content_disposition:
                        try:
                            body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except:
                            pass
                    elif content_type == 'text/html' and 'attachment' not in content_disposition:
                        try:
                            body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except:
                            pass
            else:
                content_type = msg.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body_text = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
                elif content_type == 'text/html':
                    try:
                        body_html = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
            
            return EmailMessage(
                id=message_id,
                uid=uid or message_id,
                mailbox=self.current_mailbox,
                sender=sender,
                recipient=recipient,
                subject=subject,
                timestamp=timestamp,
                size_bytes=size,
                has_attachments=has_attachments,
                flags=flags,
                headers=headers,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                raw_message=raw_message if fetch_body else None
            )
            
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        try:
            result, data = self.imap.store(message_id, '+FLAGS', '\\Seen')
            return result == 'OK'
        except Exception as e:
            logger.error(f"Error marking message {message_id} as read: {e}")
            return False
    
    def delete_message(self, message_id: str) -> bool:
        """Mark a message for deletion"""
        try:
            result, data = self.imap.store(message_id, '+FLAGS', '\\Deleted')
            if result == 'OK':
                self.imap.expunge()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            return False
    
    def move_message(self, message_id: str, dest_mailbox: str) -> bool:
        """Move a message to another mailbox"""
        try:
            # Try MOVE command first (IMAP4rev1 extension)
            result, data = self.imap.move(message_id, dest_mailbox)
            if result == 'OK':
                return True
            
            # Fallback: copy and delete
            result, data = self.imap.copy(message_id, dest_mailbox)
            if result == 'OK':
                return self.delete_message(message_id)
            
            return False
        except Exception as e:
            logger.error(f"Error moving message {message_id} to {dest_mailbox}: {e}")
            return False


class MailboxMonitor:
    """Monitor mailboxes for new messages and trigger webhooks"""
    
    def __init__(self, imap_client: IMAPClient, webhook_processor: Callable):
        self.imap_client = imap_client
        self.webhook_processor = webhook_processor
        self.monitoring = False
        self.monitor_thread = None
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        
    def start_monitoring(self, mailboxes: List[str], interval: int = 60):
        """Start monitoring specified mailboxes"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.stop_event.clear()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(mailboxes, interval),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started monitoring mailboxes: {mailboxes}")
    
    def stop_monitoring(self):
        """Stop mailbox monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logger.info("Stopped mailbox monitoring")
    
    def _monitor_loop(self, mailboxes: List[str], interval: int):
        """Main monitoring loop"""
        last_check = {}
        
        while not self.stop_event.wait(interval):
            try:
                for mailbox in mailboxes:
                    if self.stop_event.is_set():
                        break
                    
                    self._check_mailbox(mailbox, last_check.get(mailbox))
                    last_check[mailbox] = datetime.now(timezone.utc)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short delay before retrying
    
    def _check_mailbox(self, mailbox: str, last_check: Optional[datetime]):
        """Check a specific mailbox for new messages"""
        try:
            mailbox_info = self.imap_client.select_mailbox(mailbox)
            if not mailbox_info:
                return
            
            # Search for new messages
            criteria = 'UNSEEN'
            if last_check:
                # Search for messages since last check
                date_str = last_check.strftime('%d-%b-%Y')
                criteria = f'SINCE {date_str} UNSEEN'
            
            message_ids = self.imap_client.search_messages(criteria)
            
            for msg_id in message_ids:
                if self.stop_event.is_set():
                    break
                
                message = self.imap_client.fetch_message(msg_id, fetch_body=True)
                if message:
                    # Add to processing queue
                    self.message_queue.put(message)
                    
                    # Process webhook immediately for realtime triggers
                    try:
                        self.webhook_processor(message, 'realtime')
                    except Exception as e:
                        logger.error(f"Error processing webhook for message {msg_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking mailbox {mailbox}: {e}")


class MailFilterProcessor:
    """Process mail filters and determine if messages match webhook criteria"""
    
    @staticmethod
    def matches_filters(message: EmailMessage, filters: Dict[str, Any]) -> bool:
        """Check if a message matches the specified filters"""
        try:
            # Sender patterns
            sender_patterns = filters.get('sender_patterns', [])
            if sender_patterns:
                sender_match = any(
                    re.search(pattern, message.sender, re.IGNORECASE)
                    for pattern in sender_patterns
                )
                if not sender_match:
                    return False
            
            # Subject patterns
            subject_patterns = filters.get('subject_patterns', [])
            if subject_patterns:
                subject_match = any(
                    re.search(pattern, message.subject, re.IGNORECASE)
                    for pattern in subject_patterns
                )
                if not subject_match:
                    return False
            
            # Body patterns
            body_patterns = filters.get('body_patterns', [])
            if body_patterns:
                body_text = f"{message.body_text} {message.body_html}"
                body_match = any(
                    re.search(pattern, body_text, re.IGNORECASE)
                    for pattern in body_patterns
                )
                if not body_match:
                    return False
            
            # Attachment presence
            has_attachments = filters.get('has_attachments')
            if has_attachments is not None:
                if message.has_attachments != has_attachments:
                    return False
            
            # Size filters
            min_size_kb = filters.get('min_size_kb')
            if min_size_kb and message.size_bytes < (min_size_kb * 1024):
                return False
            
            max_size_kb = filters.get('max_size_kb')
            if max_size_kb and message.size_bytes > (max_size_kb * 1024):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing filters: {e}")
            return False


def format_message_payload(message: EmailMessage, payload_type: str) -> Dict[str, Any]:
    """Format message data for webhook payload"""
    if payload_type == 'RAW':
        return {
            'raw_message': message.raw_message.decode('utf-8', errors='replace') if message.raw_message else '',
            'message_id': message.id,
            'uid': message.uid,
            'mailbox': message.mailbox,
            'timestamp': message.timestamp.isoformat()
        }
    else:  # JSON format
        return {
            'message_id': message.id,
            'uid': message.uid,
            'mailbox': message.mailbox,
            'sender': message.sender,
            'recipient': message.recipient,
            'subject': message.subject,
            'timestamp': message.timestamp.isoformat(),
            'size_bytes': message.size_bytes,
            'has_attachments': message.has_attachments,
            'attachment_count': len(message.attachments),
            'flags': message.flags,
            'headers': message.headers,
            'body_text': message.body_text,
            'body_html': message.body_html,
            'attachments': message.attachments
        }
