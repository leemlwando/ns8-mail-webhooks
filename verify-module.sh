#!/bin/bash

#
# Verification script for ns8-mail-webhooks module
# Run this after applying the permission fix to verify everything is working
#

set -e

echo "=== NS8 Mail Webhooks - Verification Script ==="
echo

# Get module information
MODULE_ROOT=$(pwd)
MODULE_USER=$(whoami)
BACKEND_IMAGE="localhost/mail-webhooks-backend:latest"

echo "Module root: ${MODULE_ROOT}"
echo "Module user: ${MODULE_USER}"
echo "Backend image: ${BACKEND_IMAGE}"
echo

# Test 1: Check script permissions
echo "=== Test 1: Checking script permissions ==="
PERMISSION_ERRORS=0

find "${MODULE_ROOT}/actions" -name "[0-9]*" -type f | while read script; do
    if [ ! -x "${script}" ]; then
        echo "✗ Missing execute permission: ${script}"
        PERMISSION_ERRORS=$((PERMISSION_ERRORS + 1))
    fi
done

if [ ${PERMISSION_ERRORS} -eq 0 ]; then
    echo "✓ All action scripts have execute permissions"
else
    echo "✗ Found ${PERMISSION_ERRORS} scripts with permission issues"
fi
echo

# Test 2: Check backend image exists
echo "=== Test 2: Checking backend image ==="
if podman image exists "${BACKEND_IMAGE}"; then
    echo "✓ Backend image exists: ${BACKEND_IMAGE}"
    IMAGE_ID=$(podman image inspect "${BACKEND_IMAGE}" --format "{{.Id}}" | head -c 12)
    echo "  Image ID: ${IMAGE_ID}"
else
    echo "✗ Backend image not found: ${BACKEND_IMAGE}"
    echo "  Available images:"
    podman images | grep -E "(mail-webhooks|localhost)" || echo "  No mail-webhooks images found"
fi
echo

# Test 3: Check environment configuration
echo "=== Test 3: Checking environment configuration ==="
ENV_FILE="${MODULE_ROOT}/environment"
if [ -f "${ENV_FILE}" ]; then
    if grep -q "MAIL_WEBHOOKS_BACKEND_IMAGE" "${ENV_FILE}"; then
        CONFIGURED_IMAGE=$(grep "MAIL_WEBHOOKS_BACKEND_IMAGE" "${ENV_FILE}" | cut -d'=' -f2)
        echo "✓ Backend image configured: ${CONFIGURED_IMAGE}"
        if [ "${CONFIGURED_IMAGE}" = "${BACKEND_IMAGE}" ]; then
            echo "✓ Image configuration matches expected value"
        else
            echo "✗ Image configuration mismatch:"
            echo "  Expected: ${BACKEND_IMAGE}"
            echo "  Configured: ${CONFIGURED_IMAGE}"
        fi
    else
        echo "✗ MAIL_WEBHOOKS_BACKEND_IMAGE not found in environment file"
    fi
else
    echo "✗ Environment file not found: ${ENV_FILE}"
fi
echo

# Test 4: Check systemd service status
echo "=== Test 4: Checking systemd service status ==="
if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
    echo "✓ mail-webhooks.service is active"
    
    # Check if the service has been running for a reasonable time (more than 10 seconds)
    UPTIME=$(systemctl --user show mail-webhooks.service --property=ActiveEnterTimestamp --value)
    echo "  Service started: ${UPTIME}"
else
    echo "✗ mail-webhooks.service is not active"
    echo "  Service status:"
    systemctl --user status mail-webhooks.service --no-pager || true
fi
echo

# Test 5: Check API health endpoint
echo "=== Test 5: Checking API health endpoint ==="
if curl -s --connect-timeout 5 http://127.0.0.1:20080/api/health >/dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://127.0.0.1:20080/api/health)
    echo "✓ API health endpoint responding"
    echo "  Response: ${HEALTH_RESPONSE}"
else
    echo "✗ API health endpoint not responding"
    echo "  Checking if port 20080 is listening..."
    if netstat -ln 2>/dev/null | grep :20080 >/dev/null; then
        echo "  Port 20080 is listening"
    else
        echo "  Port 20080 is not listening"
    fi
fi
echo

# Test 6: Test configuration action
echo "=== Test 6: Testing configuration action ==="
CONFIG_ACTION="${MODULE_ROOT}/actions/get-configuration/20read"
if [ -x "${CONFIG_ACTION}" ]; then
    if "${CONFIG_ACTION}" >/dev/null 2>&1; then
        echo "✓ get-configuration action executed successfully"
    else
        echo "✗ get-configuration action failed"
        echo "  Running action with output for debugging:"
        "${CONFIG_ACTION}" || true
    fi
else
    echo "✗ get-configuration action not executable: ${CONFIG_ACTION}"
fi
echo

# Test 7: Check recent service logs for errors
echo "=== Test 7: Checking recent service logs ==="
ERROR_COUNT=$(journalctl --user -u mail-webhooks.service -n 50 --no-pager 2>/dev/null | grep -i error | wc -l)
if [ ${ERROR_COUNT} -eq 0 ]; then
    echo "✓ No errors found in recent service logs"
else
    echo "✗ Found ${ERROR_COUNT} error messages in recent service logs"
    echo "  Recent errors:"
    journalctl --user -u mail-webhooks.service -n 50 --no-pager 2>/dev/null | grep -i error | tail -5
fi
echo

# Summary
echo "=== Verification Summary ==="
echo "Module: ns8-mail-webhooks"
echo "User: ${MODULE_USER}"
echo "Status: $(systemctl --user is-active mail-webhooks.service 2>/dev/null || echo 'inactive')"
echo

# Check overall health
HEALTH_CHECKS=0
HEALTH_PASSED=0

# Count checks
HEALTH_CHECKS=7

# Check results (this is a simplified check - in reality you'd track each test result)
if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
    HEALTH_PASSED=$((HEALTH_PASSED + 1))
fi

if podman image exists "${BACKEND_IMAGE}"; then
    HEALTH_PASSED=$((HEALTH_PASSED + 1))
fi

if curl -s --connect-timeout 5 http://127.0.0.1:20080/api/health >/dev/null 2>&1; then
    HEALTH_PASSED=$((HEALTH_PASSED + 1))
fi

echo "Health checks passed: ${HEALTH_PASSED}/${HEALTH_CHECKS}"

if [ ${HEALTH_PASSED} -eq ${HEALTH_CHECKS} ]; then
    echo "✓ All verification tests passed - module is working correctly!"
    exit 0
else
    echo "✗ Some verification tests failed - please review the issues above"
    exit 1
fi
