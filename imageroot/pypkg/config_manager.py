"""
Configuration Manager for NS8 Mail Webhooks Module

Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
Licensed under GPL-3.0
"""

import os
import json
import agent
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages module configuration independently"""
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.config_dir = f"/home/{module_id}/.config"
        self.state_dir = f"{self.config_dir}/state"
        self.data_dir = f"/home/{module_id}/.local/share/webhook-data"
        
        # Ensure directories exist
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    @property
    def env_file(self) -> str:
        return f"{self.state_dir}/environment"
    
    @property
    def config_file(self) -> str:
        return f"{self.state_dir}/config.json"
    
    def read_config(self) -> Dict[str, Any]:
        """Read module configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self._get_default_config()
        except Exception:
            return self._get_default_config()
    
    def write_config(self, config: Dict[str, Any]) -> None:
        """Write module configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def read_env(self) -> Dict[str, str]:
        """Read environment variables"""
        if os.path.exists(self.env_file):
            return agent.read_envfile(self.env_file)
        return {}
    
    def write_env(self, env_vars: Dict[str, str]) -> None:
        """Write environment variables"""
        agent.write_envfile(self.env_file, env_vars)
    
    def get_data_file(self, filename: str) -> str:
        """Get path to data file"""
        return os.path.join(self.data_dir, filename)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'module_name': f'Mail Webhooks ({self.module_id})',
            'log_level': 'info',
            'max_concurrent_deliveries': 10,
            'default_timeout': 30,
            'default_retry_attempts': 3,
            'retry_delay': 60,
            'require_tls': True,
            'verify_ssl_certificates': True,
            'allowed_hosts': '',
            'preferred_mail_module': '',
            'event_subscription_mode': 'automatic',
            'enable_event_filtering': True,
            'batch_size': 10,
            'batch_delay': 1000,
            'log_retention_days': 30,
            'api_port': 3000,
            'api_memory_limit': '256M',
            'enable_api_metrics': True
        }
