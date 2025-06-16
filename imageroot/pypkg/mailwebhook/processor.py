import requests
import json
import time
import os
from typing import Dict, Set
from .storage import WebhookStorage
from .imap_client import SimpleIMAPClient

class EmailProcessor:
    def __init__(self):
        self.storage = WebhookStorage()
        self.processed_messages: Set[str] = set()
        
    def process_scheduled_jobs(self):
        """Process all active scheduled configurations"""
        configs = self.storage.get_configs(active_only=True)
        
        for config in configs:
            try:
                self._process_config(config, unread_only=True)
            except Exception as e:
                print(f"Error processing config {config['name']}: {e}")
                self.storage.log_processing(
                    config['id'], 
                    'N/A', 
                    'Scheduled Job Error',
                    'ERROR', 
                    str(e)
                )
    
    def process_one_time_job(self, config: Dict) -> Dict:
        """Process a one-time job configuration"""
        results = {
            'processed': 0,
            'errors': 0,
            'messages': []
        }
        
        try:
            processed_count = self._process_config(config, unread_only=False)
            results['processed'] = processed_count
            results['messages'].append(f"Successfully processed {processed_count} messages")
        except Exception as e:
            results['errors'] = 1
            results['messages'].append(f"Job failed: {str(e)}")
            
        return results
    
    def test_webhook(self, webhook_url: str, api_key: str = None) -> Dict:
        """Test a webhook URL with a sample payload"""
        try:
            test_payload = {
                'test': True,
                'message': 'Test webhook from ns8-mail-webhook module',
                'timestamp': time.time()
            }
            
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            response = requests.post(
                webhook_url,
                data=json.dumps(test_payload),
                headers=headers,
                timeout=10
            )
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_text': response.text[:200] if response.text else '',
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'response_text': '',
                'error': str(e)
            }
    
    def _process_config(self, config: Dict, unread_only: bool = True) -> int:
        """Process emails for a specific configuration"""
        processed_count = 0
        
        # Get IMAP credentials from environment
        imap_user = self._get_env_var('MAIL_ADMIN_USER')
        imap_pass = self._get_env_var('MAIL_ADMIN_PASS')
        
        if not imap_user or not imap_pass:
            raise Exception("IMAP credentials not configured")
        
        imap = SimpleIMAPClient()
        
        try:
            if not imap.connect(imap_user, imap_pass):
                raise Exception("Failed to connect to IMAP server")
            
            for message in imap.get_messages(config['mailbox'], unread_only):
                # Skip if already processed (for scheduled jobs)
                if unread_only and message['id'] in self.processed_messages:
                    continue
                
                try:
                    # Send to webhook
                    success = self._send_webhook(config, message)
                    
                    if success:
                        self.processed_messages.add(message['id'])
                        if unread_only:
                            imap.mark_as_read(message['id'])
                        
                        # Log success only if config has an ID (saved config)
                        if config.get('id'):
                            self.storage.log_processing(
                                config['id'],
                                message['id'],
                                message['subject'],
                                'SUCCESS'
                            )
                        processed_count += 1
                    else:
                        if config.get('id'):
                            self.storage.log_processing(
                                config['id'],
                                message['id'], 
                                message['subject'],
                                'FAILED',
                                'Webhook request failed'
                            )
                        
                except Exception as e:
                    if config.get('id'):
                        self.storage.log_processing(
                            config['id'],
                            message['id'],
                            message['subject'], 
                            'ERROR',
                            str(e)
                        )
                    
        finally:
            imap.disconnect()
            
        return processed_count
    
    def _send_webhook(self, config: Dict, message: Dict) -> bool:
        """Send message to webhook URL"""
        try:
            # Prepare payload
            if config.get('payload_format') == 'JSON':
                payload = {
                    'subject': message['subject'],
                    'from': message['from'],
                    'to': message['to'],
                    'date': message['date'],
                    'body': message['body'],
                    'message_id': message['id']
                }
                headers = {'Content-Type': 'application/json'}
                data = json.dumps(payload)
            else:  # RAW format
                headers = {'Content-Type': 'text/plain'}
                data = message['raw']
            
            # Add API key if configured
            if config.get('api_key'):
                headers['Authorization'] = f"Bearer {config['api_key']}"
            
            # Send request
            response = requests.post(
                config['webhook_url'],
                data=data,
                headers=headers,
                timeout=30
            )
            
            return response.status_code < 400
            
        except Exception as e:
            print(f"Webhook request failed: {e}")
            return False
    
    def _get_env_var(self, name: str) -> str:
        """Get environment variable with fallback"""
        return os.getenv(name, '')
