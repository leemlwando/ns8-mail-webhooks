#!/bin/bash

#
# Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
# SPDX-License-Identifier: MIT
#

# Terminate on error
set -e

# Prepare variables for later use
images=()
# The image will be pushed to GitHub container registry under leemlwando namespace
repobase="${REPOBASE:-ghcr.io/leemlwando}"
# Configure the image name
reponame="ns8-mail-webhooks"

# Create a new empty container image
container=$(buildah from scratch)

# Reuse existing nodebuilder-mail-webhooks container, to speed up builds
if ! buildah containers --format "{{.ContainerName}}" | grep -q nodebuilder-mail-webhooks; then
    echo "Pulling NodeJS runtime..."
    buildah from --name nodebuilder-mail-webhooks -v "${PWD}:/usr/src:Z" docker.io/library/node:22.16.0-slim
fi

echo "Build static UI files with node..."
buildah run \
    --workingdir=/usr/src/ui \
    --env="NODE_OPTIONS=--openssl-legacy-provider" \
    nodebuilder-mail-webhooks \
    sh -c "yarn install && yarn build"

# Add imageroot directory to the container image
buildah add "${container}" imageroot /imageroot
buildah add "${container}" ui/dist /ui

# Setup the entrypoint, ask to reserve one TCP port with the label and set a rootless container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=traefik@node:routeadm" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.images=${repobase}/mail-webhooks-backend:latest" \
    "${container}"

# Commit the image
buildah commit "${container}" "${repobase}/${reponame}"

# Append the image URL to the images array
images+=("${repobase}/${reponame}")

#
# Build the backend image
#
echo "Building backend image..."
backend_container=$(buildah from docker.io/library/python:3.9-slim)

# Copy requirements and install dependencies
buildah copy "${backend_container}" requirements.txt /tmp/
buildah run "${backend_container}" /bin/sh -c "pip install --no-cache-dir -r /tmp/requirements.txt"

# Copy backend code
buildah copy "${backend_container}" imageroot/pypkg/mailwebhook /app/

# Configure the backend image
buildah config \
    --workingdir=/app \
    --cmd='["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]' \
    --port=8000 \
    --label="org.opencontainers.image.source=https://github.com/leemlwando/ns8-mail-webhooks" \
    --label="org.opencontainers.image.authors=Lee M. Lwando <leemlwando@gmail.com>" \
    --label="org.opencontainers.image.vendor=Lee M. Lwando" \
    --label="org.opencontainers.image.licenses=MIT" \
    --label="org.opencontainers.image.title=Mail Webhooks Backend" \
    --label="org.opencontainers.image.description=NethServer 8 Mail Webhooks Module Backend" \
    "${backend_container}"

buildah commit "${backend_container}" "${repobase}/mail-webhooks-backend"
images+=("${repobase}/mail-webhooks-backend")

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
