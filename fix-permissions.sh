#!/bin/bash

#
# Fix permissions for all action scripts
#

set -e

echo "Setting execute permissions on action scripts..."

# Set execute permissions on all action scripts
find imageroot/actions -type f -name "*[0-9][0-9]*" -exec chmod +x {} \;

# Also set permissions on bin scripts
find imageroot/bin -type f -exec chmod +x {} \; 2>/dev/null || true

echo "Permissions fixed successfully"
