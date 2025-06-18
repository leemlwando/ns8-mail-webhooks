#!/bin/bash

set -e

# Redirect any output to stderr
exec 1>&2

echo "Starting container entrypoint..."

# Execute the provided command
exec "$@"
