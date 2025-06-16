#!/bin/bash

#
# Simple test script for the mail webhook backend API
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

set -e

API_BASE="http://localhost:8080/api"

echo "Testing Mail Webhook Backend API..."
echo "=================================="

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "${API_BASE}/health" | python3 -m json.tool
echo

# Test stats endpoint
echo "2. Testing stats endpoint..."
curl -s "${API_BASE}/stats" | python3 -m json.tool
echo

# Test mailboxes endpoint
echo "3. Testing mailboxes endpoint..."
curl -s "${API_BASE}/mailboxes" | python3 -m json.tool
echo

# Test triggers endpoint
echo "4. Testing triggers endpoint..."
curl -s "${API_BASE}/triggers" | python3 -m json.tool
echo

# Test jobs endpoint
echo "5. Testing jobs endpoint..."
curl -s "${API_BASE}/jobs" | python3 -m json.tool
echo

# Test logs endpoint
echo "6. Testing logs endpoint..."
curl -s "${API_BASE}/logs" | python3 -m json.tool
echo

echo "All tests completed!"
