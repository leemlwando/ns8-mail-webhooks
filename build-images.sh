#!/bin/bash

#
# Copyright (C) 2025 Nethesis S.r.l.
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

# Create a new empty container image
container=$(buildah from scratch)

# Reuse existing nodebuilder-mailwebhooks container, to speed up builds
if ! buildah containers --format "{{.ContainerName}}" | grep -q nodebuilder-mailwebhooks; then
    echo "Pulling NodeJS runtime..."
    buildah from --name nodebuilder-mailwebhooks -v "${PWD}:/usr/src:Z" docker.io/library/node:18-slim
fi

echo "Build static UI files with node..."
buildah run --env="NODE_OPTIONS=--openssl-legacy-provider" nodebuilder-mailwebhooks sh -c "cd /usr/src/ui && yarn install && yarn build"

# Set execute permissions on action scripts before adding to container
echo "Setting execute permissions on action scripts..."
find imageroot/actions -type f -name "*[0-9][0-9]*" -exec chmod +x {} \;
find imageroot/bin -type f -exec chmod +x {} \; 2>/dev/null || true
find imageroot/events -type f -name "*[0-9][0-9]*" -exec chmod +x {} \; 2>/dev/null || true
find imageroot/update-module.d -type f -exec chmod +x {} \; 2>/dev/null || true

# Add imageroot directory to the container image
buildah add "${container}" imageroot /imageroot
buildah add "${container}" ui/dist /ui

# Setup the entrypoint, ask to reserve one TCP port with the label and set a rootfull container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=traefik@node:routeadm cluster:accountconsumer" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.rootfull=0" \
    "${container}"

# Commit the image
buildah commit "${container}" "${repobase}/${reponame}"

# Append the image URL to the images array
images+=("${repobase}/${reponame}")

# Now build the API service image separately
echo "Building mail-webhooks API service image..."
api_container=$(buildah from python:3.11-slim)

# Set working directory
buildah config --workingdir /app "${api_container}"

# Copy and install requirements
buildah copy "${api_container}" imageroot/api/requirements.txt /app/
buildah run "${api_container}" pip install --no-cache-dir -r requirements.txt

# Copy application code
buildah copy "${api_container}" imageroot/api /app/

# Make scripts executable
buildah run "${api_container}" chmod +x entrypoint.sh start.sh

# Expose port and set entrypoint
buildah config --port 8080 --entrypoint '["./entrypoint.sh"]' "${api_container}"

# Commit the API image
buildah commit "${api_container}" "${repobase}/${reponame}-api"

# Append the API image URL to the images array
images+=("${repobase}/${reponame}-api")

#
# NOTICE:
#
# It is possible to build and publish multiple images.
#
# 1. create another buildah container
# 2. add things to it and commit it
# 3. append the image url to the images array
#

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
