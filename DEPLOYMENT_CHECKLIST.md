# NS8 Mail Webhooks - Deployment Checklist

## Pre-Deployment (Workstation)

- [x] ✅ Backend image configured to build locally (not pull from registry)
- [x] ✅ Environment variable `MAIL_WEBHOOKS_BACKEND_IMAGE` properly set
- [x] ✅ Action scripts have correct sequence (30ensure_backend_image before 80start_services)
- [x] ✅ All scripts have executable permissions on workstation
- [x] ✅ Line endings fixed to Unix (LF) format
- [x] ✅ build-images.sh sets proper permissions during build
- [x] ✅ Removed duplicate 85ensure_backend_image file

## Post-Deployment (Server)

### Step 1: Upload Troubleshooting Scripts
```bash
scp fix-server-permissions.sh verify-module.sh root@your-server:/tmp/
```

### Step 2: Apply Permission Fix
```bash
ssh root@your-server
su - mail-webhooks1  # Replace with your actual module instance
cd ~/.config/containers/systemd  # Or your module installation path
cp /tmp/fix-server-permissions.sh .
chmod +x fix-server-permissions.sh
./fix-server-permissions.sh
```

### Step 3: Verify Fix Applied Successfully
```bash
cp /tmp/verify-module.sh .
chmod +x verify-module.sh
./verify-module.sh
```

## Expected Results After Fix

✅ **Service Status**: `systemctl --user status mail-webhooks.service` shows "active (running)"
✅ **Image Built**: `podman image exists localhost/mail-webhooks-backend:latest` returns true
✅ **API Responding**: `curl -s http://127.0.0.1:20080/api/health` returns health status
✅ **Actions Work**: `./actions/get-configuration/20read` executes without errors
✅ **No Permission Errors**: Service logs show no "permission denied" messages
✅ **No Pull Errors**: Podman doesn't try to pull the localhost image

## Key Files Fixed

| File | Issue | Solution |
|------|-------|----------|
| `actions/*/[0-9]*` | Missing execute permissions | `chmod +x` applied to all action scripts |
| `systemd/user/*.service` | Windows CRLF line endings | Converted to Unix LF format |
| `30ensure_backend_image` | Script builds backend image locally | Moved to run before service start (sequence 30) |
| `environment` | Missing backend image variable | Added `MAIL_WEBHOOKS_BACKEND_IMAGE=localhost/mail-webhooks-backend:latest` |
| `mail-webhooks.service` | References registry image | Now uses environment variable for local image |

## Troubleshooting Commands

If issues persist after applying the fix:

```bash
# Check service logs
journalctl --user -u mail-webhooks.service -f

# Check image status
podman images | grep mail-webhooks

# Test image directly
podman run --rm -p 20080:20080 localhost/mail-webhooks-backend:latest

# Check script permissions
find actions -name "[0-9]*" -type f ! -executable

# Check environment
cat environment | grep MAIL_WEBHOOKS_BACKEND_IMAGE
```

## Module Architecture (Rootless)

- **User**: `mail-webhooks1` (or similar instance name)
- **Services**: systemd user services (not system-wide)
- **Container Runtime**: Podman rootless
- **Image Storage**: Local user registry (`localhost/mail-webhooks-backend:latest`)
- **Configuration**: `~/.config/containers/systemd/`
- **Logs**: `journalctl --user -u mail-webhooks.service`

## NS8 Compliance

✅ **Rootless Operation**: Module runs as unprivileged user
✅ **Local Image Build**: Backend image built locally, not pulled from registry
✅ **Systemd Integration**: Uses systemd user services for lifecycle management
✅ **Environment Variables**: Configuration via environment file
✅ **Action Script Sequence**: Proper numbering ensures correct execution order
✅ **Error Handling**: Scripts include proper error checking and logging

## Success Indicators

When the module is working correctly:

1. **Service starts immediately** without pulling errors
2. **Backend API responds** at http://127.0.0.1:20080/api/health
3. **Actions execute cleanly** (e.g., get-configuration, list-webhooks)
4. **Web UI accessible** via NS8 cluster manager
5. **Logs show normal operation** without permission or image errors

## Contact Information

If you continue to experience issues after following this checklist, please provide:

1. Output of `./verify-module.sh`
2. Recent service logs: `journalctl --user -u mail-webhooks.service -n 50`
3. Image status: `podman images | grep mail-webhooks`
4. Action script permissions: `ls -la actions/*/[0-9]*`
