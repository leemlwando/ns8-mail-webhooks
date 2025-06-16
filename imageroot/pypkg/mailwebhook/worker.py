#!/usr/bin/env python3

import time
import signal
import os
import sys
from mailwebhook.processor import EmailProcessor

class WebhookWorker:
    def __init__(self):
        self.processor = EmailProcessor()
        self.running = True
        
    def start(self):
        """Main worker loop"""
        print(f"Mail Webhook Worker starting (PID: {os.getpid()})")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.running:
            try:
                print("Processing scheduled jobs...")
                self.processor.process_scheduled_jobs()
                
                # Sleep for check interval (default 60 seconds)
                check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(30)  # Wait before retrying
                
        print("Mail Webhook Worker stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"Received signal {signum}, shutting down...")
        self.running = False

if __name__ == "__main__":
    worker = WebhookWorker()
    worker.start()
