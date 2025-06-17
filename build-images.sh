#!/bin/bash

#
# Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
#
# This script builds the ns8-mail-webhooks module images
#

set -e

# Build Deno webhook server image
echo "Building Deno webhook server image..."
buildah bud \
    --layers \
    --force-rm \
    --tag ghcr.io/leemlwando/ns8-mail-webhooks-server:latest \
    webhook-server/

# Build main module image  
echo "Building main module image..."
buildah bud \
    --layers \
    --force-rm \
    --tag ghcr.io/leemlwando/ns8-mail-webhooks:latest \
    imageroot/

echo "Build completed successfully!"
echo ""
echo "Images built:"
echo "  - ghcr.io/leemlwando/ns8-mail-webhooks-server:latest"
echo "  - ghcr.io/leemlwando/ns8-mail-webhooks:latest"
