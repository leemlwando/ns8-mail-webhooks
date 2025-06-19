#!/usr/bin/env python3

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""
Integration test script for NS8 mail webhooks module validation.
This script tests the mail module validation logic using the same
approach as the actual validation scripts.
"""

import sys
import os

# Add imageroot to Python path to import agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'imageroot'))

try:
    import agent
    print("✓ Agent module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import agent module: {e}")
    sys.exit(1)

def test_redis_discovery():
    """Test Redis-based mail module discovery."""
    print("\n=== Testing Redis Mail Module Discovery ===")
    
    try:
        mail_providers = []
        
        # Use Redis to find mail module services (same logic as validation script)
        with agent.redis_connect() as rdb:
            # Look for mail module service endpoints
            mail_service_keys = rdb.keys('module/mail*/srv/tcp/*')
            print(f"Found {len(mail_service_keys)} mail service keys")
            
            for key in mail_service_keys:
                try:
                    service_info = rdb.hgetall(key)
                    if service_info and service_info.get('host'):
                        # Extract module ID from key (e.g., mail1, mail2)
                        key_parts = key.split('/')
                        if len(key_parts) >= 2:
                            module_id = key_parts[1]
                            mail_providers.append({
                                'module_id': module_id,
                                'host': service_info.get('host'),
                                'port': service_info.get('port')
                            })
                            print(f"  ✓ Found mail module: {module_id} at {service_info.get('host')}:{service_info.get('port')}")
                except Exception as e:
                    print(f"  ✗ Error processing service {key}: {e}")
                    continue
        
        if mail_providers:
            print(f"✓ Discovery successful: Found {len(mail_providers)} mail module(s)")
            return True
        else:
            print("✗ No mail modules found - this would cause validation failure in NS8")
            return False
            
    except Exception as e:
        print(f"✗ Redis discovery failed: {e}")
        return False

def test_agent_logging():
    """Test correct agent logging methods."""
    print("\n=== Testing Agent Logging ===")
    
    try:
        # Test correct logging approach
        print(agent.SD_INFO + "This is an info message", file=sys.stderr)
        print(agent.SD_WARNING + "This is a warning message", file=sys.stderr)
        print("✓ Agent logging constants work correctly")
        return True
    except Exception as e:
        print(f"✗ Agent logging failed: {e}")
        return False

def test_agent_methods():
    """Test availability of required agent methods."""
    print("\n=== Testing Agent Methods ===")
    
    required_methods = [
        'redis_connect',
        'set_weight',
        'set_status',
        'SD_INFO',
        'SD_WARNING', 
        'SD_ERR'
    ]
    
    success = True
    for method in required_methods:
        if hasattr(agent, method):
            print(f"  ✓ {method} available")
        else:
            print(f"  ✗ {method} missing")
            success = False
    
    return success

def main():
    """Run all integration tests."""
    print("NS8 Mail Webhooks Module - Integration Test")
    print("=" * 50)
    
    tests = [
        ("Agent Methods", test_agent_methods),
        ("Agent Logging", test_agent_logging),
        ("Redis Discovery", test_redis_discovery),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    if all_passed:
        print("\n✓ All tests passed! The mail validation fixes should work correctly.")
    else:
        print("\n✗ Some tests failed. Check the validation logic or environment.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
