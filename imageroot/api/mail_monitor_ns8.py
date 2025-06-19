#!/usr/bin/env python3
"""
Mail Monitor Service for NS8
Background service for monitoring NS8 mail servers and triggering webhooks through NS8 API
"""

import logging
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

import requests
from pymongo import MongoClient
from bson import ObjectId

from .mail_discovery import MailServerDiscovery

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """Process and deliver webhooks for mail events"""
    
    def __init__(self, mongodb_client: MongoClient, settings: Dict[str, Any]):
        self.mongodb_client = mongodb_client
        self.settings = settings
        self.db = mongodb_client[settings.get('database_name', 'mail_webhooks')]
        
    def process_message_webhooks(self, message_data, trigger_type: str = 'realtime'):
        """Process webhooks for a received message through NS8 mail API"""
        try:
            # Get active webhooks for this trigger type
            webhooks_collection = self.db[self.settings.get('webhooks_collection', 'webhooks')]
            
            query = {
                'active': True,
                'trigger_config.trigger_type': trigger_type
            }
            
            # Filter by mailbox if specified in webhook
            if message_data.get('mailbox'):
                query['$or'] = [
                    {'trigger_config.mailboxes': {'$in': [message_data['mailbox']]}},
                    {'trigger_config.mailboxes': {'$size': 0}},  # Empty array means all mailboxes
                    {'trigger_config.mailboxes': {'$exists': False}}
                ]
            
            active_webhooks = list(webhooks_collection.find(query))
            
            for webhook in active_webhooks:
                try:
                    # Apply webhook filters
                    mail_filters = webhook.get('trigger_config', {}).get('mail_filters', {})
                    if mail_filters and not self._matches_filters(message_data, mail_filters):
                        continue
                    
                    # Format payload based on webhook settings
                    payload_type = webhook.get('payload_format', 'json')
                    payload = self._format_message_payload(message_data, payload_type)
                    
                    # Deliver webhook
                    success, response = self._deliver_webhook(webhook, payload)
                    
                    # Log webhook delivery
                    self._log_webhook_delivery(webhook, payload, success, response)
                    
                except Exception as e:
                    logger.error(f"Error processing webhook {webhook.get('_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing message webhooks: {e}")

    def _matches_filters(self, message_data: Dict, filters: Dict) -> bool:
        """Check if message matches webhook filters"""
        try:
            # Check sender filter
            if 'sender' in filters and filters['sender']:
                sender = message_data.get('from', '')
                if filters['sender'].lower() not in sender.lower():
                    return False
            
            # Check subject filter
            if 'subject' in filters and filters['subject']:
                subject = message_data.get('subject', '')
                if filters['subject'].lower() not in subject.lower():
                    return False
            
            # Check body filter
            if 'body' in filters and filters['body']:
                body = message_data.get('body', '')
                if filters['body'].lower() not in body.lower():
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching filters: {e}")
            return False

    def _format_message_payload(self, message_data: Dict, payload_type: str) -> Dict:
        """Format message data into webhook payload"""
        try:
            if payload_type == 'raw':
                return {
                    'message': message_data.get('raw_message', ''),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:  # json format
                return {
                    'from': message_data.get('from', ''),
                    'to': message_data.get('to', ''),
                    'subject': message_data.get('subject', ''),
                    'body': message_data.get('body', ''),
                    'mailbox': message_data.get('mailbox', ''),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'headers': message_data.get('headers', {}),
                    'attachments': message_data.get('attachments', [])
                }
                
        except Exception as e:
            logger.error(f"Error formatting message payload: {e}")
            return {}

    def _deliver_webhook(self, webhook: Dict, payload: Dict) -> tuple[bool, Dict]:
        """Deliver webhook to configured URL"""
        try:
            url = webhook.get('url')
            if not url:
                return False, {'error': 'No URL configured'}
            
            headers = webhook.get('headers', {})
            timeout = webhook.get('timeout', 30)
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            success = response.status_code < 400
            return success, {
                'status_code': response.status_code,
                'response_text': response.text[:1000]  # Limit response text
            }
            
        except Exception as e:
            logger.error(f"Error delivering webhook: {e}")
            return False, {'error': str(e)}

    def _log_webhook_delivery(self, webhook: Dict, payload: Dict, success: bool, response: Dict):
        """Log webhook delivery to events collection"""
        try:
            if not self.mongodb_client:
                return
            
            events_collection = self.db[self.settings.get('events_collection', 'events')]
            
            event = {
                'webhook_id': str(webhook['_id']),
                'webhook_url': webhook.get('url'),
                'payload': payload,
                'success': success,
                'response': response,
                'timestamp': datetime.now(timezone.utc)
            }
            
            events_collection.insert_one(event)
            
        except Exception as e:
            logger.error(f"Error logging webhook delivery: {e}")


class MailMonitorService:
    """Main mail monitoring service for NS8 integration"""
    
    def __init__(self):
        self.running = False
        self.mongodb_client = None
        self.webhook_processor = None
        self.mail_discovery = None
        self.settings = {}
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
    def start_service(self, mongodb_url: str, settings: Optional[Dict] = None):
        """Start the mail monitoring service"""
        try:
            if self.running:
                logger.warning("Mail monitor service is already running")
                return
            
            self.settings = settings or {}
            
            # Initialize MongoDB connection
            self.mongodb_client = MongoClient(mongodb_url)
            
            # Initialize mail discovery for NS8
            self.mail_discovery = MailServerDiscovery()
            
            # Initialize webhook processor
            self.webhook_processor = WebhookProcessor(self.mongodb_client, self.settings)
            
            # Start monitoring thread
            self.stop_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            self.running = True
            logger.info("Mail monitor service started with NS8 integration")
            
        except Exception as e:
            logger.error(f"Error starting mail monitor service: {e}")
            self.running = False
            
    def stop_service(self):
        """Stop the mail monitoring service"""
        try:
            if not self.running:
                return
            
            self.stop_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            if self.mongodb_client:
                self.mongodb_client.close()
            
            self.running = False
            logger.info("Mail monitor service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping mail monitor service: {e}")
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting NS8 mail monitor loop")
        
        while not self.stop_event.is_set():
            try:
                # Process interval-based triggers
                self._process_interval_triggers()
                
                # Check NS8 mail module status
                self._check_mail_module_status()
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(30)  # Wait before retrying
                
        logger.info("Mail monitor loop stopped")

    def _process_interval_triggers(self):
        """Process webhooks with interval-based triggers"""
        try:
            if not self.mongodb_client:
                return
            
            db = self.mongodb_client[self.settings.get('database_name', 'mail_webhooks')]
            webhooks_collection = db[self.settings.get('webhooks_collection', 'webhooks')]
            
            # Get all active interval-based webhooks
            interval_webhooks = list(webhooks_collection.find({
                'active': True,
                'trigger_config.trigger_type': 'interval'
            }))
            
            now = datetime.now(timezone.utc)
            
            for webhook in interval_webhooks:
                try:
                    # Check if it's time to process this webhook
                    last_triggered = webhook.get('last_triggered')
                    interval_seconds = webhook['trigger_config'].get('interval_seconds', 300)
                    
                    if not last_triggered or (now - last_triggered).total_seconds() >= interval_seconds:
                        self._process_interval_webhook(webhook)
                        
                except Exception as e:
                    logger.error(f"Error processing interval webhook {webhook.get('_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing interval triggers: {e}")
    
    def _process_interval_webhook(self, webhook: Dict):
        """Process a single interval-based webhook through NS8 mail API"""
        try:
            webhook_id = str(webhook['_id'])
            
            # Get email addresses from NS8 mail module for this webhook
            email_addresses = webhook.get('email_addresses', [])
            if not email_addresses:
                logger.warning(f"No email addresses configured for webhook {webhook_id}")
                return
            
            # Check for new messages through NS8 mail module
            # This would integrate with NS8 mail module API to check for new messages
            logger.info(f"Checking NS8 mail module for new messages for webhook {webhook_id}")
            
            # Update last triggered time
            if not self.mongodb_client:
                logger.error("MongoDB client not available")
                return
            db = self.mongodb_client[self.settings.get('database_name', 'mail_webhooks')]
            webhooks_collection = db[self.settings.get('webhooks_collection', 'webhooks')]
            webhooks_collection.update_one(
                {'_id': ObjectId(webhook_id)},
                {'$set': {'last_triggered': datetime.now(timezone.utc)}}
            )
            
        except Exception as e:
            logger.error(f"Error processing interval webhook: {e}")

    def _check_mail_module_status(self):
        """Check NS8 mail module status and availability"""
        try:
            if not self.mail_discovery:
                return
            
            # Discover available NS8 mail modules
            mail_servers = self.mail_discovery.discover_mail_servers()
            
            if not mail_servers:
                logger.warning("No NS8 mail modules found - service is NS8-only")
            else:
                logger.debug(f"Found {len(mail_servers)} NS8 mail servers")
                
        except Exception as e:
            logger.error(f"Error checking mail module status: {e}")


# Global service instance
mail_monitor_service = MailMonitorService()

def start_mail_monitor(mongodb_url: str, settings: Optional[Dict] = None):
    """Start the global mail monitor service"""
    mail_monitor_service.start_service(mongodb_url, settings)

def stop_mail_monitor():
    """Stop the global mail monitor service"""
    mail_monitor_service.stop_service()

def get_monitor_status() -> Dict[str, Any]:
    """Get current status of the mail monitor service"""
    return {
        'running': mail_monitor_service.running,
        'ns8_integration': True,
        'mail_discovery_active': bool(mail_monitor_service.mail_discovery),
        'settings_loaded': bool(mail_monitor_service.settings)
    }
