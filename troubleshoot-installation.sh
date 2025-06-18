#!/bin/bash

#
# Server-side module installation troubleshooting script
# Run this on the NS8 server after a failed module installation
#

echo "=== NS8 Mail Webhooks Installation Troubleshooting ==="
echo

# Check if we can find the module directory
MODULE_DIRS=$(find /home -name "ns8-mail-webhooks*" -type d 2>/dev/null)

if [ -z "$MODULE_DIRS" ]; then
    echo "❌ No module installation directories found"
    echo "This suggests the module installation failed very early"
    echo
    echo "Check NS8 cluster logs:"
    echo "  journalctl -u cluster -f"
    exit 1
fi

echo "📁 Found module directories:"
for dir in $MODULE_DIRS; do
    echo "  $dir"
done
echo

# Check the most recent module directory
LATEST_MODULE=$(echo "$MODULE_DIRS" | tail -1)
echo "🔍 Checking latest module: $LATEST_MODULE"

# Switch to the module user if possible
MODULE_USER=$(basename "$LATEST_MODULE")
if id "$MODULE_USER" >/dev/null 2>&1; then
    echo "👤 Module user: $MODULE_USER"
    
    # Check action script permissions
    echo
    echo "📜 Checking action script permissions:"
    sudo -u "$MODULE_USER" find "$LATEST_MODULE/.config/actions" -name "[0-9]*" -type f ! -executable 2>/dev/null | while read script; do
        echo "  ❌ Not executable: $script"
    done
    
    # Check if any actions are executable
    EXECUTABLE_COUNT=$(sudo -u "$MODULE_USER" find "$LATEST_MODULE/.config/actions" -name "[0-9]*" -type f -executable 2>/dev/null | wc -l)
    echo "  ✅ Executable scripts: $EXECUTABLE_COUNT"
    
    # Check recent service logs
    echo
    echo "📋 Recent module logs:"
    sudo -u "$MODULE_USER" journalctl --user -n 20 --no-pager 2>/dev/null || echo "  No user logs available"
    
    # Check if we can fix permissions
    echo
    echo "🔧 Attempting to fix permissions:"
    if sudo -u "$MODULE_USER" find "$LATEST_MODULE/.config/actions" -name "[0-9]*" -type f -exec chmod +x {} \; 2>/dev/null; then
        echo "  ✅ Fixed action script permissions"
    else
        echo "  ❌ Failed to fix permissions"
    fi
    
    if sudo -u "$MODULE_USER" find "$LATEST_MODULE/.config/bin" -type f -exec chmod +x {} \; 2>/dev/null; then
        echo "  ✅ Fixed bin script permissions"
    else
        echo "  ⚠️  No bin directory or failed to fix bin permissions"
    fi
    
else
    echo "❌ Module user '$MODULE_USER' not found"
fi

echo
echo "=== Suggested Actions ==="
echo "1. Remove the failed module installation:"
echo "   remove-module --no-preserve $MODULE_USER"
echo
echo "2. Check that the module image has correct permissions:"
echo "   podman run --rm --entrypoint='' ghcr.io/leemlwando/ns8-mail-webhooks:latest find /imageroot/actions -name '[0-9]*' -type f ! -executable"
echo
echo "3. Rebuild and reinstall the module with latest changes"
echo
echo "4. If issues persist, check cluster logs:"
echo "   journalctl -u cluster -n 50"
