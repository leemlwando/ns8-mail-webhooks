#!/bin/bash

#
# Copyright (C) 2025 Leemlwando  
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Terminate on error
set -e

# Prepare variables for later use
images=()
# The image will be pushed to GitHub container registry
repobase="${REPOBASE:-ghcr.io/leemlwando}"
# Configure the image name
reponame="ns8-mail-webhooks"

#
# Build API image using Containerfile
#
echo "Building API container..."
api_reponame="${reponame}-api"
buildah build --format=docker -f api/Containerfile \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.tcp-ports-demand=1" \
    -t "${repobase}/${api_reponame}" api
images+=("${repobase}/${api_reponame}")

# Create a new empty container image for the main module
container=$(buildah from scratch)

# Reuse existing nodebuilder-mail-webhooks container, to speed up builds
if ! buildah containers --format "{{.ContainerName}}" | grep -q nodebuilder-mail-webhooks; then
    echo "Pulling NodeJS runtime..."
    buildah from --name nodebuilder-mail-webhooks -v "${PWD}:/usr/src:Z" docker.io/library/node:18-slim
fi

echo "Build static UI files with node..."
buildah run --env="NODE_OPTIONS=--openssl-legacy-provider" nodebuilder-mail-webhooks sh -c "cd /usr/src/ui && yarn install && yarn build"

# Add imageroot directory to the container image
buildah add "${container}" imageroot /imageroot
buildah add "${container}" ui/dist /ui
# Setup the entrypoint, ask to reserve TCP ports with the label and set a rootless container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=node:fwadm traefik@node:routeadm" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.images=ghcr.io/leemlwando/ns8-mail-webhooks:${IMAGETAG:-latest} ghcr.io/leemlwando/ns8-mail-webhooks-api:${IMAGETAG:-latest}" \
    "${container}"
# Commit the image
buildah commit "${container}" "${repobase}/${reponame}"

# Append the image URL to the images array
images+=("${repobase}/${reponame}")

#
# Setup CI when pushing to Github. 
# Warning! docker::// protocol expects lowercase letters (,,)
if [[ -n "${CI}" ]]; then
    # Set output value for Github Actions
    printf "::set-output name=images::%s\n" "${images[*],,}"
else
    # Just print info for manual push
    printf "Publish the images with:\n\n"
    for image in "${images[@],,}"; do printf "  buildah push %s docker://%s:%s\n" "${image}" "${image}" "${IMAGETAG:-latest}" ; done
    printf "\n"
fi
