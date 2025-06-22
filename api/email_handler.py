"""
Email processing and IMAP IDLE handling
"""

import asyncio
import email
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import aioimaplib
import json
import aiohttp

from .models import EmailData, WebhookResponse
from .crud import LogCRUD

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Process emails and send webhook notifications"""
    
    async def process_email(self, email_data: EmailData, webhook: WebhookResponse) -> dict:
        """Process an email and send webhook notification"""
        try:
            # Prepare payload based on webhook settings
            if webhook.payload_type == "json":
                payload = {
                    "message_id": email_data.message_id,
                    "subject": email_data.subject,
                    "sender": email_data.sender,
                    "recipients": email_data.recipients,
                    "body": email_data.body,
                    "timestamp": email_data.timestamp.isoformat(),
                    "webhook_id": webhook.id
                }
            else:  # raw
                payload = email_data.body
            
            # Send webhook
            result = await self._send_webhook(webhook, payload)
            
            # Log the result
            await LogCRUD.create_log(
                webhook_id=webhook.id,
                level="info" if result["success"] else "error",
                message=f"Webhook {'sent' if result['success'] else 'failed'}: {webhook.name}",
                details=result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing email for webhook {webhook.id}: {e}")
            await LogCRUD.create_log(
                webhook_id=webhook.id,
                level="error",
                message=f"Email processing failed: {str(e)}",
                details={"error": str(e), "email_id": email_data.message_id}
            )
            raise
    
    async def _send_webhook(self, webhook: WebhookResponse, payload) -> dict:
        """Send webhook HTTP request"""
        try:
            headers = {
                "Content-Type": "application/json" if webhook.payload_type == "json" else "text/plain",
                "User-Agent": "NS8-Mail-Webhooks/1.0"
            }
            
            if webhook.api_key:
                headers["Authorization"] = f"Bearer {webhook.api_key}"
            
            async with aiohttp.ClientSession() as session:
                if webhook.payload_type == "json":
                    async with session.post(
                        str(webhook.url),
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_text = await response.text()
                        return {
                            "success": response.status < 400,
                            "status_code": response.status,
                            "response": response_text[:1000],  # Limit response size
                            "timestamp": datetime.utcnow().isoformat()
                        }
                else:
                    async with session.post(
                        str(webhook.url),
                        data=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_text = await response.text()
                        return {
                            "success": response.status < 400,
                            "status_code": response.status,
                            "response": response_text[:1000],
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class IMAPHandler:
    """Handle IMAP IDLE connections for real-time email monitoring"""
    
    def __init__(self):
        self.connections: Dict[str, aioimaplib.IMAP4_SSL] = {}
        self.monitored_emails: Dict[str, Set[str]] = {}  # email -> set of webhook_ids
        self.tasks: Dict[str, asyncio.Task] = {}
        self.processor = EmailProcessor()
    
    async def add_email_monitor(self, email_address: str, webhook_id: str):
        """Add monitoring for an email address"""
        try:
            if email_address not in self.monitored_emails:
                self.monitored_emails[email_address] = set()
            
            self.monitored_emails[email_address].add(webhook_id)
            
            # Start IMAP connection if not already running
            if email_address not in self.connections:
                await self._start_imap_idle(email_address)
                
            logger.info(f"Added email monitor for {email_address} (webhook {webhook_id})")
            
        except Exception as e:
            logger.error(f"Error adding email monitor for {email_address}: {e}")
            raise
    
    async def remove_email_monitor(self, email_address: str, webhook_id: str):
        """Remove monitoring for an email address"""
        try:
            if email_address in self.monitored_emails:
                self.monitored_emails[email_address].discard(webhook_id)
                
                # If no more webhooks monitoring this email, stop IMAP connection
                if not self.monitored_emails[email_address]:
                    await self._stop_imap_idle(email_address)
                    del self.monitored_emails[email_address]
                    
            logger.info(f"Removed email monitor for {email_address} (webhook {webhook_id})")
            
        except Exception as e:
            logger.error(f"Error removing email monitor for {email_address}: {e}")
    
    async def _start_imap_idle(self, email_address: str):
        """Start IMAP IDLE connection for an email address"""
        try:
            # Note: In a real implementation, you would need to get IMAP settings
            # This is a simplified example - you'd need to configure IMAP settings
            # based on the email provider or from configuration
            
            # For now, we'll use a polling approach instead of IMAP IDLE
            # due to complexity of managing master credentials
            task = asyncio.create_task(self._poll_email(email_address))
            self.tasks[email_address] = task
            
            logger.info(f"Started email polling for {email_address}")
            
        except Exception as e:
            logger.error(f"Error starting IMAP for {email_address}: {e}")
            raise
    
    async def _stop_imap_idle(self, email_address: str):
        """Stop IMAP IDLE connection for an email address"""
        try:
            if email_address in self.tasks:
                self.tasks[email_address].cancel()
                del self.tasks[email_address]
            
            if email_address in self.connections:
                await self.connections[email_address].close()
                del self.connections[email_address]
                
            logger.info(f"Stopped email monitoring for {email_address}")
            
        except Exception as e:
            logger.error(f"Error stopping IMAP for {email_address}: {e}")
    
    async def _poll_email(self, email_address: str):
        """Poll for new emails (simplified approach)"""
        try:
            while True:
                # In a real implementation, this would connect to IMAP
                # and check for new emails, then process them
                # For now, this is a placeholder that logs the polling
                
                logger.debug(f"Polling emails for {email_address}")
                
                # Sleep for polling interval (e.g., 30 seconds)
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info(f"Email polling cancelled for {email_address}")
        except Exception as e:
            logger.error(f"Error in email polling for {email_address}: {e}")
            # Restart polling after error
            await asyncio.sleep(60)
            if email_address in self.monitored_emails:
                asyncio.create_task(self._poll_email(email_address))
    
    async def process_new_email(self, email_data: EmailData):
        """Process a new email and trigger relevant webhooks"""
        try:
            from .crud import WebhookCRUD
            
            # Find webhooks that should be triggered by this email
            webhook_ids = self.monitored_emails.get(email_data.recipients[0], set())
            
            for webhook_id in webhook_ids:
                try:
                    webhook = await WebhookCRUD.get_webhook(webhook_id)
                    if webhook and webhook.enabled and webhook.trigger_type == "real time":
                        await self.processor.process_email(email_data, webhook)
                        
                except Exception as e:
                    logger.error(f"Error processing email for webhook {webhook_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing new email: {e}")
    
    async def close(self):
        """Close all IMAP connections"""
        try:
            # Cancel all tasks
            for task in self.tasks.values():
                task.cancel()
            
            # Close all connections
            for connection in self.connections.values():
                await connection.close()
            
            self.tasks.clear()
            self.connections.clear()
            self.monitored_emails.clear()
            
            logger.info("Closed all IMAP connections")
            
        except Exception as e:
            logger.error(f"Error closing IMAP connections: {e}")
