#!/usr/bin/env python3

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import sys
import json
import agent

# Test script to verify all agent methods are working correctly
# This should help identify any agent method calls that don't exist

print("Testing agent module methods...", file=sys.stderr)

# Test valid agent methods
try:
    # Test environment setting (this should work)
    agent.set_env("TEST_VAR", "test_value")
    print("✓ agent.set_env() working", file=sys.stderr)
    
    # Test logging constants (these should work)
    print(agent.SD_INFO + "Testing SD_INFO constant", file=sys.stderr)
    print(agent.SD_WARNING + "Testing SD_WARNING constant", file=sys.stderr) 
    print(agent.SD_ERR + "Testing SD_ERR constant", file=sys.stderr)
    print("✓ agent logging constants working", file=sys.stderr)
    
    # Test status setting (this should work)
    agent.set_status('validation-passed')
    print("✓ agent.set_status() working", file=sys.stderr)
    
    # Test redis connection (this should work)
    with agent.redis_connect() as rdb:
        print("✓ agent.redis_connect() working", file=sys.stderr)
    
    print("All agent methods test passed successfully", file=sys.stderr)
    
except AttributeError as e:
    print(f"AttributeError in agent method test: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"General error in agent method test: {e}", file=sys.stderr)
    sys.exit(1)
