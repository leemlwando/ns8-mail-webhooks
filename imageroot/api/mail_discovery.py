#!/usr/bin/env python3
"""
NS8 Mail Server Discovery Service
Discovers and integrates with NS8 mail modules using agent and Redis
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
import agent
import agent.tasks

logger = logging.getLogger(__name__)

class MailServerDiscovery:
    """Discover and manage NS8 mail server integrations"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def discover_mail_servers(self) -> List[Dict[str, Any]]:
        """Discover available NS8 mail servers using Redis service discovery"""
        try:
            mail_servers = []
            
            # Use Redis to discover mail service providers directly
            with agent.redis_connect() as rdb:
                # Look for mail module service endpoints
                mail_service_keys = rdb.keys('module/mail*/srv/tcp/*')
                
                for key in mail_service_keys:
                    try:
                        service_info = rdb.hgetall(key)
                        if service_info and service_info.get('host'):
                            # Extract module ID from key (e.g., mail1, mail2)
                            key_parts = key.split('/')
                            if len(key_parts) >= 2:
                                module_id = key_parts[1]
                                server_info = {
                                    'module_id': module_id,
                                    'host': service_info.get('host', 'localhost'),
                                    'port': int(service_info.get('port', 143)),
                                    'service_type': 'ns8-mail',
                                    'available': True,
                                    'integration_method': 'agent_tasks'
                                }
                                mail_servers.append(server_info)
                                
                    except Exception as e:
                        logger.error(f"Error processing mail service {key}: {e}")
                        continue
            
            if not mail_servers:
                logger.warning("No NS8 mail modules found via service discovery")
                
            return mail_servers
            
        except Exception as e:
            logger.error(f"Error discovering mail servers: {e}")
            return []
            return []
    
    def get_mail_server_by_id(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Get specific mail server by module ID"""
        try:
            mail_servers = self.discover_mail_servers()
            for server in mail_servers:
                if server.get('module_id') == module_id:
                    return server
            return None
            
        except Exception as e:
            logger.error(f"Error getting mail server {module_id}: {e}")
            return None
    
    def get_email_addresses(self, module_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available email addresses from NS8 mail module"""
        try:
            if not module_id:
                # Find first available mail module
                mail_servers = self.discover_mail_servers()
                if not mail_servers:
                    logger.error("No NS8 mail modules found")
                    return []
                module_id = mail_servers[0]['module_id']
            
            # Call NS8 mail module to get email addresses
            try:
                result = agent.tasks.run(
                    agent_id=f'{module_id}@node',
                    action='list-addresses',
                    data={}
                )
                
                if result.get('exit_code', 0) == 0:
                    addresses_data = json.loads(result.get('output', '{}'))
                    return addresses_data.get('addresses', [])
                else:
                    logger.error(f"Failed to get addresses from {module_id}: {result.get('error', 'Unknown error')}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error calling mail module {module_id}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting email addresses: {e}")
            return []
    
    def get_user_mailboxes(self, module_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available user mailboxes from NS8 mail module"""
        try:
            if not module_id:
                # Find first available mail module
                mail_servers = self.discover_mail_servers()
                if not mail_servers:
                    logger.error("No NS8 mail modules found")
                    return []
                module_id = mail_servers[0]['module_id']
            
            # Call NS8 mail module to get user mailboxes
            try:
                result = agent.tasks.run(
                    agent_id=f'{module_id}@node',
                    action='list-user-mailboxes',
                    data={}
                )
                
                if result.get('exit_code', 0) == 0:
                    mailboxes_data = json.loads(result.get('output', '{}'))
                    return mailboxes_data.get('mailboxes', [])
                else:
                    logger.error(f"Failed to get mailboxes from {module_id}: {result.get('error', 'Unknown error')}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error calling mail module {module_id}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting user mailboxes: {e}")
            return []
    
    def test_mail_integration(self, module_id: Optional[str] = None) -> Dict[str, Any]:
        """Test integration with NS8 mail module"""
        try:
            result = {
                'success': False,
                'module_id': module_id,
                'mail_servers_found': 0,
                'addresses_found': 0,
                'mailboxes_found': 0,
                'errors': []
            }
            
            # Discover mail servers
            mail_servers = self.discover_mail_servers()
            result['mail_servers_found'] = len(mail_servers)
            
            if not mail_servers:
                result['errors'].append('No NS8 mail modules found')
                return result
            
            # Use specified module or first available
            target_module = module_id
            if not target_module:
                target_module = mail_servers[0]['module_id']
            
            result['module_id'] = target_module
            
            # Test email addresses
            addresses = self.get_email_addresses(target_module)
            result['addresses_found'] = len(addresses)
            
            # Test mailboxes
            mailboxes = self.get_user_mailboxes(target_module)
            result['mailboxes_found'] = len(mailboxes)
            
            # Success if we found addresses or mailboxes
            result['success'] = (result['addresses_found'] > 0 or result['mailboxes_found'] > 0)
            
            if not result['success']:
                result['errors'].append('No email addresses or mailboxes found')
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing mail integration: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': [str(e)]
            }

# Global instance
mail_discovery = MailServerDiscovery()
