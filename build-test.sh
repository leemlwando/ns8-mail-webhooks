#!/bin/bash

#
# Copyright (C) 2025 Lee M. Lwando
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Terminate on error
set -e

# Prepare variables for later use
images=()
# The image will be pushed to GitHub container registry
repobase="${REPOBASE:-ghcr.io/leemlwando}"
# Configure the image name
reponame="mail-webhooks"

# Create a new empty container image
container=$(buildah from scratch)

echo "Skipping UI build for testing..."

# Add imageroot directory to the container image
buildah add "${container}" imageroot /imageroot

# Create a minimal UI directory to satisfy the container structure
mkdir -p ui/dist
echo '<!DOCTYPE html><html><head><title>Mail Webhooks</title></head><body><h1>Mail Webhooks Module</h1><p>Backend testing mode - UI disabled</p></body></html>' > ui/dist/index.html

buildah add "${container}" ui/dist /ui

# Setup the entrypoint, ask to reserve one TCP port with the label and set a rootless container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=traefik@node:routeadm" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.images=docker.io/jmalloc/echo-server:latest" \
    "${container}"

# Commit the image
buildah commit "${container}" "${repobase}/${reponame}"

# Append the image URL to the images array
images+=("${repobase}/${reponame}")

# Clean up temporary UI files
rm -rf ui/dist

echo "Build completed successfully!"
printf "Image built: %s\n" "${repobase}/${reponame}"

# Just print info for manual testing
printf "\nTo add the module to NS8:\n"
printf "  add-module ghcr.io/leemlwando/mail-webhooks:latest\n\n"
