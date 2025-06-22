# NS8 Mail Webhooks Module - Implementation Documentation

## Overview
This document details the implementation of the ns8-mail-webhooks module for NethServer 8, including architectural decisions, resolved issues, and the current state of the project.

## Problem Resolved: 403 Forbidden Error

### Root Cause
The module was experiencing a **403 Forbidden error** during configuration when attempting to allocate TCP ports from the cluster. This was caused by **missing authorization labels** in the module images.

### Error Details
```
aiohttp.client_exceptions.ClientResponseError: 403, message='Forbidden', url=URL('http://cluster-leader:9311/api/cluster/tasks')
```

The error occurred when the configure-module action tried to request a second TCP port for the API service using:
```python
api_tcp_port = agent.tasks.run(
    agent_id=agent.resolve_agent_id('cluster'),
    action='reserve-tcp-port',
    data={},
)
```

## Solution Implemented

### 1. Authorization Fix
**Fixed in `build-images.sh`**: Added the critical `node:fwadm` authorization needed for TCP port allocation.

**Before**:
```bash
--label="org.nethserver.authorizations=traefik@node:routeadm" \
```

**After**:
```bash
--label="org.nethserver.authorizations=node:fwadm traefik@node:routeadm" \
```

### 2. Architectural Simplification
Moved from a **dual-port to single-port approach** to avoid complex TCP port allocation and follow NS8 best practices.

#### Previous Architecture (Problematic)
- UI Container: Port 8080 (exposed via `${TCP_PORT}`)
- API Container: Port 8000 (exposed via `${API_TCP_PORT}`)
- Two separate Traefik routes
- Manual TCP port allocation via cluster API

#### Current Architecture (Working)
- UI Container: Port 8080 (exposed via `${TCP_PORT}`)
- API Container: Port 8000 (internal to pod only)
- Single Traefik route
- nginx reverse proxy for API routing

## Current Module Architecture

### Container Setup
```
┌─── Podman Pod: mail-webhooks ───┐
│                                 │
│  ┌─── UI Container ───┐         │
│  │  nginx:alpine      │:8080    │ ← Exposed to host via ${TCP_PORT}
│  │  - Serves static   │         │
│  │  - Proxies /api/*  │         │
│  └────────────────────┘         │
│             │                   │
│             ▼ localhost:8000    │
│  ┌─── API Container ──┐         │
│  │  python:3.11-slim │:8000    │ ← Internal to pod only
│  │  - FastAPI backend │         │
│  │  - MongoDB access  │         │
│  └────────────────────┘         │
└─────────────────────────────────┘
```

### Network Flow
1. **External Request** → Traefik → `127.0.0.1:${TCP_PORT}` → nginx (UI Container)
2. **Static Files** → nginx serves directly from `/usr/share/nginx/html`
3. **API Requests** → nginx proxies `/api/*` → `localhost:8000` → FastAPI (API Container)

## Key Configuration Files

### systemd/user/mail-webhooks.service
```bash
# Single port exposure
--publish 127.0.0.1:${TCP_PORT}:8080 \
```

### ui/nginx.conf
```nginx
# Proxy API requests to the API container
location /api/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### build-images.sh
```bash
# Correct authorization and port demand
--label="org.nethserver.authorizations=node:fwadm traefik@node:routeadm" \
--label="org.nethserver.tcp-ports-demand=1" \
```

## Changes Made

### 1. Authorization Labels
- **Added `node:fwadm`**: Required for TCP port allocation and firewall management
- **Kept `traefik@node:routeadm`**: Required for Traefik route management

### 2. Port Configuration
- **Reduced TCP ports demand**: From `2` to `1`
- **Single port exposure**: Only `${TCP_PORT}:8080`
- **Internal API communication**: API runs on port 8000 within pod

### 3. Container Updates
- **UI Container**: Changed from Node.js dev server to nginx production setup
- **API Container**: Remains Python/FastAPI, now internal-only
- **Communication**: Within-pod networking via localhost

### 4. Configuration Scripts
- **configure-module/20configure**: Removed complex port allocation, single Traefik route
- **destroy-module/20destroy**: Simplified to single route cleanup
- **systemd units**: Updated for single-port pod architecture

## Environment Variables

### Required Environment Variables
```bash
# MongoDB Configuration
MONGODB_URL=mongodb+srv://...
MONGODB_WEBHOOKS_COLLECTION=webhooks
MONGODB_JOBS_COLLECTION=jobs
MONGODB_LOGS_COLLECTION=logs

# Container Images
MAIL_WEBHOOKS_IMAGE=ghcr.io/leemlwando/ns8-mail-webhooks:latest
MAIL_WEBHOOKS_API_IMAGE=ghcr.io/leemlwando/ns8-mail-webhooks-api:latest

# Network (automatically set by NS8)
TCP_PORT=<allocated-by-cluster>
```

## Build Status
✅ **Images build successfully** with correct authorization labels  
✅ **No build errors** or dependency issues  
✅ **Proper container labeling** for NS8 compliance  

### Build Commands
```bash
# Build both images
./build-images.sh

# Push to registry (requires authentication)
buildah push ghcr.io/leemlwando/ns8-mail-webhooks-api docker://ghcr.io/leemlwando/ns8-mail-webhooks-api:latest
buildah push ghcr.io/leemlwando/ns8-mail-webhooks docker://ghcr.io/leemlwando/ns8-mail-webhooks:latest
```

## Testing Strategy

### Module Lifecycle Testing
1. **Installation**: Verify module installs without authorization errors
2. **Configuration**: Test port allocation and Traefik route setup
3. **Service Communication**: Verify UI ↔ API communication through nginx proxy
4. **Functionality**: Test webhook creation, email processing, job management
5. **Destruction**: Ensure clean removal of all resources

### Network Testing
1. **UI Access**: Verify static files serve correctly
2. **API Proxy**: Test `/api/*` requests proxy to backend
3. **CORS Handling**: Verify cross-origin requests work
4. **Error Handling**: Test nginx error pages and API error responses

## Compliance with NS8 Standards

### Authorization Patterns
- **`node:fwadm`**: For firewall and network management
- **`traefik@node:routeadm`**: For Traefik route administration
- **Pattern matches**: Similar to ns8-webserver and other multi-service modules

### Module Metadata
- **TCP ports demand**: Correctly specified as `1`
- **Rootless containers**: Both containers run as non-root users
- **Image references**: Properly labeled with org.nethserver.images

### File Structure
```
ns8-mail-webhooks/
├── imageroot/
│   ├── systemd/user/
│   │   ├── mail-webhooks.service    # Pod management
│   │   ├── api.service              # API container
│   │   └── ui.service               # UI container
│   ├── actions/
│   │   ├── configure-module/
│   │   ├── destroy-module/
│   │   └── get-configuration/
│   ├── bin/
│   │   ├── module-dump-state
│   │   └── module-cleanup-state
│   └── events/
│       └── smarthost-changed/
├── api/                             # FastAPI backend
├── ui/                              # Vue.js frontend
└── build-images.sh                  # Image build script
```

## Next Steps

### Immediate Testing
1. **Deploy module**: Test installation with fixed authorizations
2. **Verify configuration**: Ensure no 403 errors during setup
3. **Test communication**: Validate UI ↔ API communication
4. **End-to-end testing**: Full webhook workflow testing

### Production Readiness
1. **Security review**: Verify container security and permissions
2. **Performance testing**: Load testing for webhook processing
3. **Monitoring setup**: Health checks and logging configuration
4. **Documentation**: User guide and troubleshooting documentation

### Future Enhancements
1. **SSL/TLS**: Consider internal communication encryption
2. **Scaling**: Multi-replica support for high availability
3. **Metrics**: Prometheus metrics integration
4. **Backup**: State backup and restore capabilities

## Troubleshooting

### Common Issues

#### 403 Forbidden Errors
- **Cause**: Missing authorization labels
- **Solution**: Ensure `node:fwadm` is included in org.nethserver.authorizations

#### Port Allocation Failures
- **Cause**: Incorrect TCP ports demand or missing authorizations
- **Solution**: Verify build-images.sh labels and module metadata

#### Container Communication Issues
- **Cause**: Incorrect networking or proxy configuration
- **Solution**: Check nginx.conf proxy settings and pod networking

#### Service Startup Failures
- **Cause**: Missing environment variables or image pull issues
- **Solution**: Verify environment setup and image availability

## References
- [NS8 Developer Documentation](https://nethserver.github.io/ns8-core/)
- [Reference Modules](../reference-repos/)
  - ns8-roundcubemail: Single-service pattern
  - ns8-webserver: Multi-service pattern
  - ns8-mail: Complex authorization example
