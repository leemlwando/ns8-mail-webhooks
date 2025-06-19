#!/usr/bin/env python3

#
# Test script for NS8 mail module integration
#

import json
import sys
import os
import agent

def test_redis_connection():
    """Test Redis connection and list mail module keys"""
    try:
        with agent.redis_connect() as rdb:
            print("✓ Redis connection successful")
            
            # List all keys to understand the structure
            all_keys = rdb.keys('*')
            mail_keys = [key for key in all_keys if 'mail' in key]
            
            print(f"Found {len(all_keys)} total Redis keys")
            print(f"Found {len(mail_keys)} mail-related keys:")
            
            for key in mail_keys[:10]:  # Show first 10
                print(f"  {key}")
            
            if len(mail_keys) > 10:
                print(f"  ... and {len(mail_keys) - 10} more")
              # Look specifically for mail module service endpoints
            mail_service_keys = rdb.keys('module/mail*/srv/tcp/*')
            print(f"\nFound {len(mail_service_keys)} mail service endpoints:")
            for key in mail_service_keys:
                info = rdb.hgetall(key)
                print(f"  {key}: {info}")
            
            return True
            
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

def test_agent_tasks():
    """Test if agent.tasks module is available"""
    try:
        import agent.tasks
        print("✓ agent.tasks module is available")
        return True
    except ImportError as e:
        print(f"✗ agent.tasks module not available: {e}")
        return False

def test_mail_module_call():
    """Test calling a mail module action"""
    try:
        import agent.tasks
        
        # Try to call list-domains action on mail1 module
        result = agent.tasks.run(
            agent_id='mail1@node',
            action='list-domains',
            data={}
        )
        
        print("✓ Successfully called mail module action")
        print(f"Result: {json.dumps(result, indent=2)}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to call mail module action: {e}")
        return False

if __name__ == "__main__":
    print("NS8 Mail Module Integration Test")
    print("=" * 40)
    
    # Test 1: Redis connection
    print("\n1. Testing Redis connection...")
    redis_ok = test_redis_connection()
    
    # Test 2: Agent tasks availability
    print("\n2. Testing agent.tasks availability...")
    tasks_ok = test_agent_tasks()
    
    # Test 3: Mail module call (only if previous tests pass)
    if redis_ok and tasks_ok:
        print("\n3. Testing mail module action call...")
        call_ok = test_mail_module_call()
    else:
        print("\n3. Skipping mail module test (prerequisites failed)")
        call_ok = False
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"  Redis connection: {'✓' if redis_ok else '✗'}")
    print(f"  Agent tasks:     {'✓' if tasks_ok else '✗'}")
    print(f"  Mail module call: {'✓' if call_ok else '✗'}")
    
    if redis_ok and tasks_ok and call_ok:
        print("\n🎉 All tests passed! Mail integration should work.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check NS8 environment.")
        sys.exit(1)
