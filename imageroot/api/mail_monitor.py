#!/usr/bin/env python3
"""
Mail Monitor Service
Background service for monitoring mail servers and triggering webhooks
"""

import asyncio
import logging
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import requests
from pymongo import MongoClient
from bson import ObjectId

from .mail_discovery import MailServerDiscovery
from .imap_integration import IMAPClient, MailboxMonitor, MailFilterProcessor, format_message_payload

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """Process and deliver webhooks for mail events"""
    
    def __init__(self, mongodb_client: MongoClient, settings: Dict[str, Any]):
        self.mongodb_client = mongodb_client
        self.settings = settings
        self.db = mongodb_client[settings.get('database_name', 'mail_webhooks')]
        
    def process_message_webhooks(self, message, trigger_type: str = 'realtime'):
        """Process webhooks for a received message"""
        try:
            # Get active webhooks for this trigger type
            webhooks_collection = self.db[self.settings.get('webhooks_collection', 'webhooks')]
            
            query = {
                'active': True,
                'trigger_config.trigger_type': trigger_type
            }
            
            # Filter by mailbox if specified in webhook
            if message.mailbox:
                query['$or'] = [
                    {'trigger_config.mailboxes': {'$in': [message.mailbox]}},
                    {'trigger_config.mailboxes': {'$size': 0}},  # Empty array means all mailboxes
                    {'trigger_config.mailboxes': {'$exists': False}}
                ]
            
            webhooks = list(webhooks_collection.find(query))
            
            for webhook in webhooks:
                try:
                    self._process_single_webhook(webhook, message)
                except Exception as e:
                    logger.error(f"Error processing webhook {webhook.get('_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing message webhooks: {e}")
    
    def _process_single_webhook(self, webhook: Dict, message):
        """Process a single webhook for a message"""
        webhook_id = str(webhook['_id'])
        
        try:
            # Check mail filters
            mail_filters = webhook.get('mail_filters', {})
            if mail_filters and not MailFilterProcessor.matches_filters(message, mail_filters):
                logger.debug(f"Message {message.id} doesn't match filters for webhook {webhook_id}")
                return
            
            # Format payload
            payload_type = webhook.get('payload_type', 'JSON')
            payload = format_message_payload(message, payload_type)
            
            # Add webhook metadata
            webhook_data = {
                'webhook_id': webhook_id,
                'webhook_name': webhook['name'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger_type': webhook['trigger_config']['trigger_type'],
                'message': payload
            }
            
            # Deliver webhook
            success, response_data = self._deliver_webhook(webhook, webhook_data)
            
            # Log execution
            self._log_webhook_execution(webhook_id, message, success, response_data)
            
            # Apply post-processing actions if webhook was successful
            if success:
                self._apply_post_actions(webhook, message)
                
        except Exception as e:
            logger.error(f"Error processing webhook {webhook_id} for message {message.id}: {e}")
            self._log_webhook_execution(webhook_id, message, False, {'error': str(e)})
    
    def _deliver_webhook(self, webhook: Dict, payload: Dict) -> tuple[bool, Dict]:
        """Deliver webhook payload to the configured URL"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NS8-MailWebhooks/1.0'
            }
            
            # Add API key if configured
            api_key = webhook.get('api_key', '').strip()
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Send request with timeout and retries
            max_retries = self.settings.get('max_retries', 3)
            retry_delay = self.settings.get('retry_delay', 60)
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    response = requests.post(
                        str(webhook['url']),
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    response_time = time.time() - start_time
                    
                    success = response.status_code < 400
                    
                    return success, {
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'response_body': response.text[:1000],  # Limit response body size
                        'attempt': attempt + 1
                    }
                    
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False, {'error': 'Request timeout', 'attempt': attempt + 1}
                    
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False, {'error': 'Connection error', 'attempt': attempt + 1}
                    
        except Exception as e:
            return False, {'error': str(e)}
    
    def _log_webhook_execution(self, webhook_id: str, message, success: bool, response_data: Dict):
        """Log webhook execution to database"""
        try:
            logs_collection = self.db[self.settings.get('logs_collection', 'logs')]
            
            log_entry = {
                'webhook_id': webhook_id,
                'timestamp': datetime.now(timezone.utc),
                'status': 'success' if success else 'failed',
                'processed_message_id': message.id,
                'mailbox': message.mailbox,
                'message_sender': message.sender,
                'message_subject': message.subject,
                'response_data': response_data
            }
            
            logs_collection.insert_one(log_entry)
            
            # Update webhook execution stats
            webhooks_collection = self.db[self.settings.get('webhooks_collection', 'webhooks')]
            update_data = {
                '$inc': {'execution_count': 1},
                '$set': {
                    'last_triggered': datetime.now(timezone.utc),
                    'last_execution_status': 'success' if success else 'failed'
                }
            }
            
            webhooks_collection.update_one(
                {'_id': ObjectId(webhook_id)},
                update_data
            )
            
        except Exception as e:
            logger.error(f"Error logging webhook execution: {e}")
    
    def _apply_post_actions(self, webhook: Dict, message):
        """Apply post-processing actions after successful webhook delivery"""
        try:
            post_actions = webhook.get('post_actions', {})
            if not post_actions:
                return
            
            # Get IMAP client (this should be passed or managed by the monitor)
            # For now, we'll log the actions that should be applied
            actions_applied = {}
            
            if post_actions.get('mark_as_read'):
                # This should be handled by the IMAP client
                logger.info(f"Should mark message {message.id} as read")
                actions_applied['mark_as_read'] = True
            
            if post_actions.get('delete_message'):
                logger.info(f"Should delete message {message.id}")
                actions_applied['delete_message'] = True
            
            move_to_folder = post_actions.get('move_to_folder')
            if move_to_folder:
                logger.info(f"Should move message {message.id} to folder {move_to_folder}")
                actions_applied['move_to_folder'] = move_to_folder
            
            add_flag = post_actions.get('add_flag')
            if add_flag:
                logger.info(f"Should add flag {add_flag} to message {message.id}")
                actions_applied['add_flag'] = add_flag
            
            # Log applied actions
            if actions_applied:
                events_collection = self.db[self.settings.get('events_collection', 'events')]
                event = {
                    'webhook_id': str(webhook['_id']),
                    'message_id': message.id,
                    'mailbox': message.mailbox,
                    'timestamp': datetime.now(timezone.utc),
                    'post_actions_applied': actions_applied
                }
                events_collection.insert_one(event)
                
        except Exception as e:
            logger.error(f"Error applying post actions: {e}")


class MailMonitorService:
    """Main service for monitoring mail servers and processing webhooks"""
    
    def __init__(self):
        self.running = False
        self.mongodb_client = None
        self.settings = {}
        self.mail_discovery = MailServerDiscovery()
        self.active_monitors = {}  # mail_server_uuid -> MailboxMonitor
        self.webhook_processor = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
    def load_settings(self) -> bool:
        """Load settings from MongoDB"""
        try:
            if not self.mongodb_client:
                return False
            
            db = self.mongodb_client['mail_webhooks']
            settings_collection = db['settings']
            
            settings_doc = settings_collection.find_one({})
            if settings_doc:
                self.settings = settings_doc
                logger.info("Loaded settings from database")
                return True
            else:
                logger.warning("No settings found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return False
    
    def connect_mongodb(self, mongodb_url: str) -> bool:
        """Connect to MongoDB"""
        try:
            self.mongodb_client = MongoClient(mongodb_url)
            # Test connection
            self.mongodb_client.admin.command('ping')
            logger.info("Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def start_service(self, mongodb_url: str):
        """Start the mail monitoring service"""
        if self.running:
            return
        
        # Connect to MongoDB
        if not self.connect_mongodb(mongodb_url):
            raise Exception("Failed to connect to MongoDB")
        
        # Load settings
        if not self.load_settings():
            logger.warning("No settings loaded, using defaults")
        
        # Initialize webhook processor
        self.webhook_processor = WebhookProcessor(self.mongodb_client, self.settings)
        
        # Start monitoring
        self.running = True
        self.stop_event.clear()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Mail monitor service started")
    
    def stop_service(self):
        """Stop the mail monitoring service"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        
        # Stop all active monitors
        for monitor in self.active_monitors.values():
            try:
                monitor.stop_monitoring()
            except Exception as e:
                logger.error(f"Error stopping monitor: {e}")
        
        self.active_monitors.clear()
        
        # Wait for monitor thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        # Close MongoDB connection
        if self.mongodb_client:
            self.mongodb_client.close()
            self.mongodb_client = None
        
        logger.info("Mail monitor service stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_config_check = datetime.now(timezone.utc)
        config_check_interval = timedelta(minutes=5)  # Check for config changes every 5 minutes
        
        while not self.stop_event.wait(30):  # Check every 30 seconds
            try:
                # Periodically reload settings and webhook configurations
                now = datetime.now(timezone.utc)
                if now - last_config_check > config_check_interval:
                    self.load_settings()
                    self._update_monitors()
                    last_config_check = now
                
                # Process interval-based triggers
                self._process_interval_triggers()
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)
    
    def _update_monitors(self):
        """Update active monitors based on current webhook configurations"""
        try:
            if not self.mongodb_client:
                return
            
            db = self.mongodb_client['mail_webhooks']
            webhooks_collection = db[self.settings.get('webhooks_collection', 'webhooks')]
            
            # Get all active webhooks with realtime triggers
            active_webhooks = list(webhooks_collection.find({
                'active': True,
                'trigger_config.trigger_type': 'realtime'
            }))
            
            # Determine which mail servers need monitoring
            required_servers = set()
            for webhook in active_webhooks:
                mail_server_uuid = self.settings.get('mail_server_uuid')
                if mail_server_uuid:
                    required_servers.add(mail_server_uuid)
            
            # Start monitors for required servers
            for server_uuid in required_servers:
                if server_uuid not in self.active_monitors:
                    self._start_monitor_for_server(server_uuid)
            
            # Stop monitors for servers no longer needed
            for server_uuid in list(self.active_monitors.keys()):
                if server_uuid not in required_servers:
                    self._stop_monitor_for_server(server_uuid)                    
        except Exception as e:
            logger.error(f"Error updating monitors: {e}")

    def _start_monitor_for_server(self, server_uuid: str):
        """Start monitoring for a specific mail server"""
        try:
            # Discover mail server
            mail_server = self.mail_discovery.get_mail_server_by_uuid(server_uuid)
            if not mail_server:
                logger.error(f"Mail server {server_uuid} not found")
                return
            
            # Create IMAP client
            imap_client = IMAPClient(
                host=mail_server['host'],
                port=mail_server['imap_port'],
                use_ssl=mail_server['imap_port'] == 993
            )
            
            # Connect and authenticate (credentials would need to be configured)
            # For now, we'll log that monitoring would start
            logger.info(f"Would start monitoring mail server {server_uuid} at {mail_server['host']}")
              # Create monitor with webhook processor
            if not self.webhook_processor:
                logger.error(f"Webhook processor not initialized")
                return
            monitor = MailboxMonitor(imap_client, self.webhook_processor.process_message_webhooks)
            
            # Determine which mailboxes to monitor from active webhooks
            monitored_mailboxes = self._get_monitored_mailboxes_for_server(server_uuid)
            if not monitored_mailboxes:
                monitored_mailboxes = ['INBOX']  # Default to INBOX if no specific mailboxes configured
            
            # Start monitoring the determined mailboxes
            monitor.start_monitoring(monitored_mailboxes, interval=60)
            
            self.active_monitors[server_uuid] = monitor
            logger.info(f"Started monitoring mailboxes {monitored_mailboxes} on server {server_uuid}")
            
        except Exception as e:
            logger.error(f"Error starting monitor for server {server_uuid}: {e}")

    def _stop_monitor_for_server(self, server_uuid: str):
        """Stop monitoring for a specific mail server"""
        try:
            monitor = self.active_monitors.get(server_uuid)
            if monitor:
                monitor.stop_monitoring()
                del self.active_monitors[server_uuid]
                logger.info(f"Stopped monitoring mail server {server_uuid}")
        except Exception as e:
            logger.error(f"Error stopping monitor for server {server_uuid}: {e}")

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
        """Process a single interval-based webhook"""
        try:
            webhook_id = str(webhook['_id'])
            
            # Get mail server for this webhook
            mail_server_uuid = self.settings.get('mail_server_uuid')
            if not mail_server_uuid:
                logger.warning(f"No mail server configured for webhook {webhook_id}")
                return
            
            mail_server = self.mail_discovery.get_mail_server_by_uuid(mail_server_uuid)
            if not mail_server:
                logger.error(f"Mail server {mail_server_uuid} not found for webhook {webhook_id}")
                return
              # This would connect to IMAP and check for messages matching webhook criteria
            # For now, we'll log that the interval check would occur
            logger.info(f"Would perform interval check for webhook {webhook_id}")
            
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
    
    def _get_monitored_mailboxes_for_server(self, server_uuid: str) -> List[str]:
        """Get list of mailboxes that need monitoring for a specific server"""
        try:
            if not self.mongodb_client:
                return []
            
            db = self.mongodb_client[self.settings.get('database_name', 'mail_webhooks')]
            webhooks_collection = db[self.settings.get('webhooks_collection', 'webhooks')]
            
            # Get all active realtime webhooks for this server
            active_webhooks = list(webhooks_collection.find({
                'active': True,
                'trigger_config.trigger_type': 'realtime'
                # Note: In a more complete implementation, you'd filter by server_uuid
            }))
            
            monitored_mailboxes = set()
            
            for webhook in active_webhooks:
                trigger_config = webhook.get('trigger_config', {})
                mailboxes = trigger_config.get('mailboxes', [])
                
                if not mailboxes:
                    # Empty mailboxes means monitor all default mailboxes
                    monitored_mailboxes.update(['INBOX'])
                else:
                    # Add specific mailboxes
                    monitored_mailboxes.update(mailboxes)
            
            return list(monitored_mailboxes) if monitored_mailboxes else ['INBOX']
            
        except Exception as e:
            logger.error(f"Error determining monitored mailboxes for server {server_uuid}: {e}")
            return ['INBOX']  # Default fallback


# Global service instance
mail_monitor_service = MailMonitorService()

def start_mail_monitor(mongodb_url: str):
    """Start the global mail monitor service"""
    mail_monitor_service.start_service(mongodb_url)

def stop_mail_monitor():
    """Stop the global mail monitor service"""
    mail_monitor_service.stop_service()

def get_monitor_status() -> Dict[str, Any]:
    """Get current status of the mail monitor service"""
    return {
        'running': mail_monitor_service.running,
        'active_monitors': len(mail_monitor_service.active_monitors),
        'monitored_servers': list(mail_monitor_service.active_monitors.keys()),
        'settings_loaded': bool(mail_monitor_service.settings)
    }
