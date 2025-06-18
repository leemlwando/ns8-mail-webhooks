#!/usr/bin/env python3
"""
Mail Server Discovery Service
Discovers NS8 mail server instances via Redis service discovery
"""

import redis
import json
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MailServerDiscovery:
    """Discover and manage connections to NS8 mail servers"""
    
    def __init__(self, redis_host='127.0.0.1', redis_port=6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
    
    def connect_redis(self):
        """Connect to Redis for service discovery"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis for service discovery")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    def discover_mail_servers(self) -> List[Dict]:
        """Discover available NS8 mail server instances"""
        if not self.redis_client:
            if not self.connect_redis():
                return []
        
        mail_servers = []
        
        try:
            # Find IMAP service endpoints - NS8 pattern: module/mail[1-9]*/srv/tcp/imap
            imap_keys = self.redis_client.keys('module/mail[1-9]*/srv/tcp/imap')
            
            for key in imap_keys:
                try:
                    # Extract module ID from key (e.g., mail1, mail2)
                    parts = key.split('/')
                    module_id = parts[1]  # mail1, mail2, etc.
                    
                    # Get service information
                    service_info = self.redis_client.hgetall(key)
                    
                    if service_info:
                        # Also look for submission service for completeness
                        submission_key = f"module/{module_id}/srv/tcp/submission"
                        submission_info = self.redis_client.hgetall(submission_key)
                        
                        mail_server = {
                            'module_id': module_id,
                            'uuid': service_info.get('uuid', ''),
                            'host': service_info.get('host', ''),
                            'imap_port': int(service_info.get('port', 143)),
                            'submission_port': int(submission_info.get('port', 587)) if submission_info else 587,
                            'node': service_info.get('node', ''),
                            'user_domain': service_info.get('user_domain', ''),
                            'status': 'available'
                        }
                        
                        # Validate required fields
                        if mail_server['host'] and mail_server['uuid']:
                            mail_servers.append(mail_server)
                            logger.info(f"Discovered mail server: {module_id} at {mail_server['host']}")
                        else:
                            logger.warning(f"Incomplete mail server info for {module_id}")
                            
                except Exception as e:
                    logger.error(f"Error processing mail server key {key}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error discovering mail servers: {e}")
        
        logger.info(f"Discovered {len(mail_servers)} mail servers")
        return mail_servers
    
    def get_mail_server_by_uuid(self, uuid: str) -> Optional[Dict]:
        """Get specific mail server by UUID"""
        servers = self.discover_mail_servers()
        for server in servers:
            if server['uuid'] == uuid:
                return server
        return None
    
    def validate_mail_server_connection(self, server_info: Dict) -> bool:
        """Validate that we can connect to a mail server"""
        try:
            import socket
            
            # Test IMAP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server_info['host'], server_info['imap_port']))
            sock.close()
            
            if result == 0:
                logger.info(f"Mail server {server_info['module_id']} is reachable")
                return True
            else:
                logger.warning(f"Mail server {server_info['module_id']} is not reachable")
                return False
                
        except Exception as e:
            logger.error(f"Error validating mail server connection: {e}")
            return False

# Global instance
mail_discovery = MailServerDiscovery()

def get_available_mail_servers() -> List[Dict]:
    """Get list of available mail servers"""
    return mail_discovery.discover_mail_servers()

def get_mail_server_by_uuid(uuid: str) -> Optional[Dict]:
    """Get mail server by UUID"""
    return mail_discovery.get_mail_server_by_uuid(uuid)

def validate_mail_server(uuid: str) -> bool:
    """Validate mail server connection"""
    server = get_mail_server_by_uuid(uuid)
    if server:
        return mail_discovery.validate_mail_server_connection(server)
    return False

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    
    print("Discovering mail servers...")
    servers = get_available_mail_servers()
    
    print(f"\nFound {len(servers)} mail servers:")
    for server in servers:
        print(f"  {server['module_id']}: {server['host']}:{server['imap_port']} (UUID: {server['uuid'][:8]}...)")
        if validate_mail_server(server['uuid']):
            print(f"    ✓ Connection OK")
        else:
            print(f"    ✗ Connection failed")
