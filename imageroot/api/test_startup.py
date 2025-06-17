#!/usr/bin/env python3
"""
Test script to validate the Mail Webhooks API can start properly
"""

import os
import sys
import subprocess
import tempfile
import time

def test_api_startup():
    """Test if the API can start successfully"""
    
    print("Testing Mail Webhooks API startup...")
    
    # Test MongoDB connection
    mongodb_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    print(f"Testing MongoDB connection to: {mongodb_url}")
    
    try:
        from pymongo import MongoClient
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise an exception if can't connect
        print("✓ MongoDB connection successful")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False
    
    # Test FastAPI imports
    try:
        from fastapi import FastAPI
        from uvicorn import run
        print("✓ FastAPI/Uvicorn imports successful")
    except ImportError as e:
        print(f"✗ FastAPI/Uvicorn import failed: {e}")
        return False
    
    # Test app import
    try:
        sys.path.insert(0, '/app' if os.path.exists('/app/app.py') else './imageroot/api')
        import app
        print("✓ App import successful")
    except ImportError as e:
        print(f"✗ App import failed: {e}")
        return False
    
    print("✓ All tests passed - API should start successfully")
    return True

if __name__ == "__main__":
    # Set environment variables if not set
    if not os.environ.get("MONGODB_URL"):
        os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
    if not os.environ.get("MAIL_SERVER_UUID"):
        os.environ["MAIL_SERVER_UUID"] = "test-uuid"
    
    # Set default collection names
    collections = {
        "WEBHOOKS_COLLECTION": "webhooks",
        "EVENTS_COLLECTION": "events", 
        "SETTINGS_COLLECTION": "settings",
        "TRIGGERS_COLLECTION": "triggers",
        "LOGS_COLLECTION": "logs"
    }
    
    for key, default in collections.items():
        if not os.environ.get(key):
            os.environ[key] = default
    
    success = test_api_startup()
    sys.exit(0 if success else 1)
