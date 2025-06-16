#!/usr/bin/env python3
"""
Simple test script to verify the Mail Webhooks API endpoints

This script tests the basic functionality of the API without requiring
the full NethServer 8 environment.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add the imageroot/pypkg directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "imageroot" / "pypkg"))

def test_api_endpoints():
    """Test the Mail Webhooks API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Mail Webhooks API...")
    print(f"Base URL: {base_url}")
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"\n✓ Status endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Version: {data.get('version', 'N/A')}")
            print(f"  - Status: {data.get('status', 'N/A')}")
            print(f"  - Scheduler: {data.get('scheduler_running', 'N/A')}")
    except requests.exceptions.ConnectionError:
        print("\n✗ Status endpoint: Connection failed (API server not running?)")
    except Exception as e:
        print(f"\n✗ Status endpoint: Error - {e}")
    
    # Test schedules endpoint
    try:
        response = requests.get(f"{base_url}/api/schedules/", timeout=5)
        print(f"\n✓ Schedules endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Number of schedules: {len(data)}")
    except requests.exceptions.ConnectionError:
        print("\n✗ Schedules endpoint: Connection failed")
    except Exception as e:
        print(f"\n✗ Schedules endpoint: Error - {e}")
    
    # Test logs endpoint
    try:
        response = requests.get(f"{base_url}/api/logs/", timeout=5)
        print(f"\n✓ Logs endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Number of log entries: {len(data)}")
    except requests.exceptions.ConnectionError:
        print("\n✗ Logs endpoint: Connection failed")
    except Exception as e:
        print(f"\n✗ Logs endpoint: Error - {e}")

def check_dependencies():
    """Check if required dependencies are available"""
    print("\nChecking dependencies...")
    
    try:
        import fastapi
        print(f"✓ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("✗ FastAPI: Not installed")
    
    try:
        import sqlalchemy
        print(f"✓ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError:
        print("✗ SQLAlchemy: Not installed")
    
    try:
        import schedule
        print(f"✓ Schedule: {schedule.__version__}")
    except ImportError:
        print("✗ Schedule: Not installed")

if __name__ == "__main__":
    print("Mail Webhooks API Test Script")
    print("=" * 40)
    
    check_dependencies()
    test_api_endpoints()
    
    print("\nNote: To start the API server for testing, run:")
    print("cd imageroot/pypkg && python -m mailwebhook.main")
