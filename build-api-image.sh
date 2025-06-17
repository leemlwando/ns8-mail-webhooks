#!/bin/bash

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Build the mail-webhooks API container image

set -e

repobase="${REPOBASE:-ghcr.io/leemlwando}"
IMAGETAG="${IMAGETAG:-latest}"

# Build the API container
echo "Building mail-webhooks API container..."
podman build \
    --layers=false \
    --tag="${repobase}/ns8-mail-webhooks-api:${IMAGETAG}" \
    imageroot/api/

echo "Built ${repobase}/ns8-mail-webhooks-api:${IMAGETAG}"
