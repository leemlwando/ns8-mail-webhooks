#!/bin/bash

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Terminate on error
set -e

# Prepare variables for later use
images=()
# The image will be pushed to GitHub container registry
repobase="${REPOBASE:-ghcr.io/nethserver}"
# Configure the image name
reponame="mail-webhooks"

# Build the backend application container
echo "Building mail webhook backend container..."
container=$(buildah from python:3.11-slim)

# Install system dependencies
buildah run "${container}" -- /bin/sh -c "apt-get update && apt-get install -y --no-install-recommends && rm -rf /var/lib/apt/lists/*"

# Create app user
buildah run "${container}" -- useradd --system --create-home --shell /bin/bash mailwebhook

# Set working directory
buildah config --workingdir /app "${container}"

# Copy requirements and install Python dependencies
buildah copy "${container}" requirements.txt /app/
buildah run "${container}" -- pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
buildah copy "${container}" imageroot/pypkg /app/

# Create data directory with proper permissions
buildah run "${container}" -- /bin/sh -c "mkdir -p /var/lib/nethserver/mail-webhook && chown -R mailwebhook:mailwebhook /var/lib/nethserver/mail-webhook /app"

# Configure container
buildah config --user mailwebhook "${container}"
buildah config --port 8080 "${container}"
buildah config --cmd "python -m mailwebhook.main" "${container}"

# Add health check
buildah config --healthcheck "CMD python -c \"import requests; requests.get('http://localhost:8080/api/health', timeout=5)\"" "${container}"
buildah config --healthcheck-interval 30s "${container}"
buildah config --healthcheck-timeout 10s "${container}"
buildah config --healthcheck-start-period 5s "${container}"
buildah config --healthcheck-retries 3 "${container}"

# Commit the backend image
buildah commit "${container}" "${repobase}/${reponame}:latest"
images+=("${repobase}/${reponame}")

# Build UI container
echo "Building UI container..."
# Reuse existing nodebuilder-mail-webhooks container, to speed up builds
if ! buildah containers --format "{{.ContainerName}}" | grep -q nodebuilder-mail-webhooks; then
    echo "Pulling NodeJS runtime..."
    buildah from --name nodebuilder-mail-webhooks -v "${PWD}:/usr/src:Z" docker.io/library/node:18-alpine
fi

echo "Build static UI files with node..."
buildah run \
    --workingdir=/usr/src/ui \
    --env="NODE_OPTIONS=--openssl-legacy-provider" \
    nodebuilder-mail-webhooks \
    sh -c "npm install && npm run build"

# Create UI container
ui_container=$(buildah from scratch)
buildah add "${ui_container}" imageroot /imageroot
buildah add "${ui_container}" ui/dist /ui

# Setup the entrypoint, ask to reserve one TCP port with the label and set a rootless container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=traefik@node:routeadm" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.images=${repobase}/${reponame}:latest" \
    "${ui_container}"

# Commit the UI image  
buildah commit "${ui_container}" "${repobase}/${reponame}"
images+=("${repobase}/${reponame}")

#
# Setup CI when pushing to Github. 
# Warning! docker::// protocol expects lowercase letters (,,)
if [[ -n "${CI}" ]]; then
    # Set output value for Github Actions
    printf "images=%s\n" "${images[*],,}" >> "${GITHUB_OUTPUT}"
else
    # Just print info for manual push
    printf "Publish the images with:\n\n"
    for image in "${images[@],,}"; do printf "  buildah push %s docker://%s:%s\n" "${image}" "${image}" "${IMAGETAG:-latest}" ; done
    printf "\n"
fi
