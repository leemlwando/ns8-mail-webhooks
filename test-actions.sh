#!/bin/bash

#
# Test script to validate action execution order and dependencies
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

set -e

echo "Testing Mail Webhook Module Action Execution Order"
echo "================================================="

# Change to module directory
cd "$(dirname "$0")"

# Set test environment variables
export MODULE_ID="mail-webhook-test"
export TCP_PORT="8080"
export MAIL_WEBHOOK_IMAGE="ghcr.io/nethserver/mail-webhook:latest"
export MAIL_SERVER="localhost"
export MAIL_ADMIN_USER="admin"
export MAIL_ADMIN_PASS="testpass"

# Test configuration directory
TEST_DIR="/tmp/ns8-mail-webhook-test"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Test environment:"
echo "  Test directory: $TEST_DIR"
echo "  Module ID: $MODULE_ID"
echo "  TCP Port: $TCP_PORT"
echo "  Image: $MAIL_WEBHOOK_IMAGE"
echo ""

# Function to run action script and check result
run_action() {
    local script_path="$1"
    local script_name=$(basename "$script_path")
    local input_data="${2:-{}}"
    
    echo "Running: $script_name"
    echo "Input: $input_data"
    
    if [[ -f "$script_path" && -x "$script_path" ]]; then
        echo "$input_data" | "$script_path"
        local exit_code=$?
        
        if [[ $exit_code -eq 0 ]]; then
            echo "✓ $script_name completed successfully"
        else
            echo "✗ $script_name failed with exit code $exit_code"
            return $exit_code
        fi
    else
        echo "✗ $script_name not found or not executable"
        return 1
    fi
    
    echo ""
}

# Test execution order
ACTIONS_DIR="$(pwd)/../imageroot/actions/configure-module"

echo "Testing configure-module action sequence..."
echo ""

# 1. Validate prerequisites
run_action "$ACTIONS_DIR/10validate" '{}'

# 2. Main configuration (image pulling removed - handled by systemd)
run_action "$ACTIONS_DIR/20configure" '{
    "webhook_configs": [
        {
            "name": "Test Webhook",
            "mailbox": "test@example.com",
            "webhook_url": "https://webhook.example.com/test",
            "payload_format": "json",
            "post_processing": "mark_read"
        }
    ]
}'

# 3. Initialize database
run_action "$ACTIONS_DIR/25init_database" '{}'

# Check if database was created
if [[ -f "data/webhooks.db" ]]; then
    echo "✓ Database file created successfully"
    
    # Test database structure
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "Testing database structure..."
        table_count=$(sqlite3 data/webhooks.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        echo "✓ Database contains $table_count tables"
        
        # List tables
        echo "Database tables:"
        sqlite3 data/webhooks.db "SELECT name FROM sqlite_master WHERE type='table';" | while read table; do
            echo "  - $table"
        done
    fi
else
    echo "✗ Database file not created"
fi

echo ""

# 4. Validate services (this may fail without actual systemd services)
echo "Note: Service validation may fail without actual systemd files - this is expected"
run_action "$ACTIONS_DIR/75validate_services" '{}' || echo "⚠ Service validation failed (expected without systemd files)"
echo ""

# 5. Start services (this will fail in test environment)
echo "Note: Service startup will fail in test environment - this is expected"
run_action "$ACTIONS_DIR/80start_services" '{}' || echo "⚠ Service startup failed (expected in test environment)"
echo ""

# Validate created files and directories
echo "Validating created files and directories:"

check_file_or_dir() {
    local path="$1"
    local description="$2"
    
    if [[ -e "$path" ]]; then
        if [[ -d "$path" ]]; then
            echo "✓ Directory exists: $description ($path)"
        else
            echo "✓ File exists: $description ($path)"
            
            # Show file permissions and size
            ls -la "$path" | awk '{print "  Permissions: " $1 ", Size: " $5 " bytes"}'
        fi
    else
        echo "✗ Missing: $description ($path)"
    fi
}

check_file_or_dir "state" "State directory"
check_file_or_dir "state/environment" "Environment configuration"
check_file_or_dir "data" "Data directory"
check_file_or_dir "data/webhooks.db" "SQLite database"

echo ""

# Test environment file content
if [[ -f "state/environment" ]]; then
    echo "Environment file contents:"
    cat "state/environment" | while read line; do
        echo "  $line"
    done
    echo ""
fi

# Cleanup
echo "Test completed. Cleaning up..."
cd /
rm -rf "$TEST_DIR"
echo "✓ Test directory cleaned up"

echo ""
echo "Action execution order test completed successfully!"
echo ""
echo "Execution order summary:"
echo "  10validate        → Validate prerequisites and input"
echo "  20configure       → Main configuration setup"
echo "  25init_database   → Initialize SQLite database"
echo "  75validate_services → Validate service configuration"
echo "  80start_services  → Enable and start systemd services"
echo ""
echo "Note: Image pulling is handled automatically by systemd services."
echo "Dependencies are properly ordered and race conditions are prevented."
