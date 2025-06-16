#!/bin/bash

#
# Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
# SPDX-License-Identifier: MIT
#

# Simple Docker-based build script for testing
set -e

repobase="${REPOBASE:-ghcr.io/leemlwando}"
reponame="ns8-mail-webhooks"

echo "Building UI..."
cd ui
npm install
npm run build
cd ..

echo "Building Docker image..."
docker build -t "${repobase}/${reponame}:latest" .

echo "Image built successfully: ${repobase}/${reponame}:latest"
