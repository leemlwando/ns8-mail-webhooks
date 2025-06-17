"""
Mail Configuration Manager for NS8 Webhooks Module

Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
Licensed under GPL-3.0
"""

import json
import logging
import agent
from typing import Dict, Optional, Any

logger = logging.getLogger('mail_config')

class MailConfigManager:
    """Manages mail authentication configuration retrieval"""
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.redis_ctx = agent.connect_redis()
    
    def get_mail_config(self, mail_module_id: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get complete mail configuration for IMAP/SMTP access"""
        try:
            # Method 1: Query specific mail module directly
            if mail_module_id:
                return self._get_config_from_module(mail_module_id, user_context)
            
            # Method 2: Auto-discover mail services
            return self._discover_mail_service(user_context)
            
        except Exception as e:
            logger.error(f"Failed to get mail configuration: {e}")
            raise Exception(f"Cannot retrieve mail configuration: {e}")
    
    def _get_config_from_module(self, mail_module_id: str, user_context: Optional[Dict]) -> Dict[str, Any]:
        """Get configuration from a specific mail module"""
        try:
            # Query mail module for public configuration
            public_config = agent.call_module_action(
                self.redis_ctx,
                mail_module_id,
                'get-public-service-config',
                {}
            )
            
            if not public_config or public_config.get('status') != 'success':
                raise Exception(f"Mail module {mail_module_id} not accessible")
            
            config = public_config.get('config', {})
            
            # Get service endpoints
            imap_config = config.get('imap', {})
            smtp_config = config.get('smtp', {})
            
            # Handle different authentication scenarios
            auth_config = self._resolve_authentication(mail_module_id, user_context, config)
            
            return {
                'mail_module': mail_module_id,
                'imap_host': imap_config.get('host', 'localhost'),
                'imap_port': imap_config.get('port', 993),
                'imap_tls': imap_config.get('tls', True),
                'smtp_host': smtp_config.get('host', 'localhost'),
                'smtp_port': smtp_config.get('port', 587),
                'smtp_tls': smtp_config.get('tls', True),
                **auth_config
            }
            
        except Exception as e:
            logger.error(f"Failed to get config from module {mail_module_id}: {e}")
            raise
    
    def _resolve_authentication(self, mail_module_id: str, user_context: Optional[Dict], config: Dict) -> Dict[str, str]:
        """Resolve authentication credentials based on configuration"""
        
        auth_method = config.get('auth_method', 'user_credentials')
        
        if auth_method == 'service_account':
            # Use service account credentials
            return self._get_service_account_auth(mail_module_id, config)
        
        elif auth_method == 'user_credentials':
            # Use individual user credentials
            return self._get_user_credentials_auth(user_context, config)
        
        elif auth_method == 'master_user':
            # Use master user with impersonation
            return self._get_master_user_auth(mail_module_id, user_context, config)
        
        else:
            raise Exception(f"Unsupported authentication method: {auth_method}")
    
    def _get_service_account_auth(self, mail_module_id: str, config: Dict) -> Dict[str, str]:
        """Get service account credentials"""
        try:
            # Request service account credentials from mail module
            auth_response = agent.call_module_action(
                self.redis_ctx,
                mail_module_id,
                'get-service-credentials',
                {
                    'requesting_module': self.module_id,
                    'purpose': 'webhook_processing'
                }
            )
            
            if auth_response.get('status') != 'success':
                raise Exception("Service account authentication failed")
            
            credentials = auth_response.get('credentials', {})
            
            return {
                'imap_user': credentials.get('username'),
                'imap_password': credentials.get('password'),
                'auth_method': 'service_account'
            }
            
        except Exception as e:
            logger.error(f"Service account auth failed: {e}")
            raise
    
    def _get_user_credentials_auth(self, user_context: Optional[Dict], config: Dict) -> Dict[str, str]:
        """Get user-provided credentials"""
        if not user_context:
            raise Exception("User credentials required but not provided")
        
        username = user_context.get('username')
        password = user_context.get('password')
        
        if not username or not password:
            raise Exception("Username and password required for user authentication")
        
        return {
            'imap_user': username,
            'imap_password': password,
            'auth_method': 'user_credentials'
        }
    
    def _get_master_user_auth(self, mail_module_id: str, user_context: Optional[Dict], config: Dict) -> Dict[str, str]:
        """Get master user credentials with impersonation"""
        try:
            target_user = user_context.get('target_user') if user_context else None
            
            # Request master user credentials
            auth_response = agent.call_module_action(
                self.redis_ctx,
                mail_module_id,
                'get-master-credentials',
                {
                    'requesting_module': self.module_id,
                    'target_user': target_user,
                    'purpose': 'webhook_processing'
                }
            )
            
            if auth_response.get('status') != 'success':
                raise Exception("Master user authentication failed")
            
            credentials = auth_response.get('credentials', {})
            
            # Handle different master user formats
            master_user = credentials.get('master_user')
            master_password = credentials.get('master_password')
            
            if target_user and config.get('supports_impersonation'):
                # Use impersonation syntax (Dovecot style: master_user*target_user)
                imap_user = f"{master_user}*{target_user}"
            else:
                imap_user = master_user
            
            return {
                'imap_user': imap_user,
                'imap_password': master_password,
                'auth_method': 'master_user',
                'target_user': target_user
            }
            
        except Exception as e:
            logger.error(f"Master user auth failed: {e}")
            raise
    
    def _discover_mail_service(self, user_context: Optional[Dict]) -> Dict[str, Any]:
        """Auto-discover available mail services"""
        try:
            # Query for available mail service providers
            providers = agent.list_service_providers(
                self.redis_ctx,
                service_types=['imap', 'smtp']
            )
            
            mail_providers = [p for p in providers if p['module'].startswith('mail')]
            
            if not mail_providers:
                raise Exception("No mail services found in cluster")
            
            # Use the first available mail service
            primary_provider = mail_providers[0]
            
            logger.info(f"Auto-discovered mail service: {primary_provider['module']}")
            
            return self._get_config_from_module(primary_provider['module'], user_context)
            
        except Exception as e:
            logger.error(f"Mail service discovery failed: {e}")
            raise
