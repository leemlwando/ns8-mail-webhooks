"""
IMAP client for email processing and webhook forwarding

Author: Lee M. Lwando <leemlwando@gmail.com>
Repository: https://github.com/leemlwando/ns8-mail-webhooks
"""

import imaplib
import email
import json
import base64
import logging
from email.header import decode_header
from email.utils import parsedate_to_datetime
import requests
from typing import Dict, List, Any, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IMAPProcessor:
    """IMAP client for processing emails and sending webhooks"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("IMAP_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("IMAP_PORT", "993"))
        self.timeout = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
        
    def _decode_header(self, header: str) -> str:
        """Safely decode email header"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_string += part
                
        return decoded_string
    
    def _parse_email_to_json(self, raw_email: bytes) -> Dict[str, Any]:
        """Parse raw email to structured JSON"""
        msg = email.message_from_bytes(raw_email)
        
        email_data = {
            "from": self._decode_header(msg.get("From", "")),
            "to": self._decode_header(msg.get("To", "")),
            "cc": self._decode_header(msg.get("Cc", "")),
            "subject": self._decode_header(msg.get("Subject", "")),
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
            "body_text": "",
            "body_html": "",
            "attachments": []
        }
        
        # Parse date
        try:
            if email_data["date"]:
                email_data["date"] = parsedate_to_datetime(email_data["date"]).isoformat()
        except:
            pass
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            if content_type == "text/plain":
                                email_data["body_text"] = payload.decode("utf-8", errors="ignore")
                            elif content_type == "text/html":
                                email_data["body_html"] = payload.decode("utf-8", errors="ignore")
                    except:
                        continue
                else:
                    # Handle attachments
                    filename = part.get_filename()
                    if filename:
                        try:
                            attachment_data = {
                                "filename": self._decode_header(filename),
                                "content_type": content_type,
                                "size": len(part.get_payload(decode=True) or b""),
                                "data": base64.b64encode(part.get_payload(decode=True) or b"").decode()
                            }
                            email_data["attachments"].append(attachment_data)
                        except:
                            continue
        else:
            # Single part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    content_type = msg.get_content_type()
                    if content_type == "text/plain":
                        email_data["body_text"] = payload.decode("utf-8", errors="ignore")
                    elif content_type == "text/html":
                        email_data["body_html"] = payload.decode("utf-8", errors="ignore")
            except:
                pass
        
        return email_data
    
    def _send_webhook(self, webhook_url: str, data: Any, api_key: Optional[str] = None, 
                     payload_format: str = "RAW") -> bool:
        """Send data to webhook URL"""
        try:
            headers = {"User-Agent": "NethServer-MailWebhooks/1.0"}
            
            if payload_format == "JSON":
                headers["Content-Type"] = "application/json"
                if isinstance(data, bytes):
                    # Convert raw email to JSON
                    data = json.dumps(self._parse_email_to_json(data))
                elif isinstance(data, dict):
                    data = json.dumps(data)
            else:
                headers["Content-Type"] = "message/rfc822"
            
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                webhook_url, 
                headers=headers, 
                data=data, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Webhook sent successfully to {webhook_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
            return False
    
    def process_mailbox(self, mailbox_user: str, mailbox_password: str, 
                       webhook_url: str, api_key: Optional[str] = None,
                       payload_format: str = "RAW", post_scrape_action: str = "mark_as_read",
                       process_all: bool = False) -> Dict[str, Any]:
        """Process emails in a mailbox and send to webhook"""
        
        result = {
            "status": "success",
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "errors": []
        }
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(mailbox_user, mailbox_password)
            mail.select("inbox")
            
            # Search for emails
            search_criteria = "ALL" if process_all else "UNSEEN"
            status, messages = mail.search(None, search_criteria)
            
            if status != "OK":
                raise Exception("Failed to search for emails")
            
            email_ids = messages[0].split()
            result["processed_count"] = len(email_ids)
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    raw_email = msg_data[0][1]
                    
                    # Send to webhook
                    if self._send_webhook(webhook_url, raw_email, api_key, payload_format):
                        result["success_count"] += 1
                        
                        # Apply post-scrape action
                        if post_scrape_action == "delete":
                            mail.store(email_id, "+FLAGS", "\\Deleted")
                        else:
                            mail.store(email_id, "+FLAGS", "\\Seen")
                    else:
                        result["error_count"] += 1
                        result["errors"].append(f"Failed to send webhook for email {email_id}")
                        # Mark as seen to avoid reprocessing
                        mail.store(email_id, "+FLAGS", "\\Seen")
                        
                except Exception as e:
                    result["error_count"] += 1
                    result["errors"].append(f"Error processing email {email_id}: {str(e)}")
                    logger.error(f"Error processing email {email_id}: {e}")
            
            # Expunge deleted emails
            if post_scrape_action == "delete":
                mail.expunge()
            
            mail.close()
            mail.logout()
            
            # Determine final status
            if result["error_count"] == 0:
                result["status"] = "success"
            elif result["success_count"] > 0:
                result["status"] = "partial"
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"IMAP connection failed: {str(e)}")
            logger.error(f"IMAP error for {mailbox_user}: {e}")
        
        return result
