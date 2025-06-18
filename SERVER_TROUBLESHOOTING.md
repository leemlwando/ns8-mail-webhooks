# Server-Side Troubleshooting Guide for NS8 Mail Webhooks

## Current Issues Identified

Based on the server logs, there are two main issues:

1. **Permission denied errors** on action scripts (e.g., `30ensure_backend_image`, `10read`)
2. **Podman repeatedly trying to pull** the localhost image instead of using the locally built one

## Root Cause

The permission errors prevent the `30ensure_backend_image` script from executing, which means the backend image is never built. When the systemd service tries to start, Podman attempts to pull the image from a registry (which doesn't exist) instead of using a locally built image.

## Fix Procedure

### Option 1: Automated Fix (Recommended)

1. **Copy the fix script to the server:**
   ```bash
   # On your workstation (in the project directory)
   scp fix-server-permissions.sh root@your-server:/tmp/
   ```

2. **Run the fix script on the server:**
   ```bash
   # SSH to your server as root
   ssh root@your-server
   
   # Switch to the module user (e.g., mail-webhooks1)
   su - mail-webhooks1
   
   # Navigate to the module directory
   cd /home/mail-webhooks1/.config/containers/systemd
   
   # Copy and run the fix script
   cp /tmp/fix-server-permissions.sh .
   chmod +x fix-server-permissions.sh
   ./fix-server-permissions.sh
   ```

### Option 2: Manual Fix

If you prefer to fix manually, follow these steps:

1. **SSH to the server and switch to the module user:**
   ```bash
   ssh root@your-server
   su - mail-webhooks1  # Replace with your actual module user
   cd ~/.config/containers/systemd  # Or wherever your module is installed
   ```

2. **Fix script permissions:**
   ```bash
   # Fix all action scripts
   find ./actions -name "[0-9]*" -type f -exec chmod +x {} \;
   
   # Fix bin scripts
   find ./bin -type f -exec chmod +x {} \;
   
   # Fix any shell scripts
   find . -name "*.sh" -type f -exec chmod +x {} \;
   ```

3. **Fix line endings (if needed):**
   ```bash
   # Convert Windows line endings to Unix
   find . -type f \( -name "*.service" -o -name "*.sh" -o -name "[0-9]*" \) \
     -exec sed -i 's/\r$//' {} \;
   ```

4. **Stop existing services:**
   ```bash
   systemctl --user stop mail-webhooks.service
   systemctl --user stop mail-monitor.service
   ```

5. **Clean up and rebuild the backend image:**
   ```bash
   # Remove existing backend image
   podman rmi localhost/mail-webhooks-backend:latest 2>/dev/null || true
   
   # Build the backend image
   cd api
   podman build -t localhost/mail-webhooks-backend:latest .
   
   # Verify the image was built
   podman image exists localhost/mail-webhooks-backend:latest && echo "Image built successfully"
   ```

6. **Set environment variable:**
   ```bash
   cd ..  # Back to module root
   echo "MAIL_WEBHOOKS_BACKEND_IMAGE=localhost/mail-webhooks-backend:latest" >> environment
   ```

7. **Restart services:**
   ```bash
   systemctl --user daemon-reload
   systemctl --user start mail-webhooks.service
   ```

8. **Verify the fix:**
   ```bash
   # Check service status
   systemctl --user status mail-webhooks.service
   
   # Check recent logs
   journalctl --user -u mail-webhooks.service -n 20
   
   # Test configuration action
   ./actions/get-configuration/20read
   
   # Test API health endpoint
   curl -s http://127.0.0.1:20080/api/health
   ```

## Expected Results After Fix

After applying the fix, you should see:

1. **No permission denied errors** in the logs
2. **Backend image builds successfully** during module configuration
3. **Systemd service starts without pulling errors**
4. **API health endpoint responds** at `http://127.0.0.1:20080/api/health`
5. **Module actions execute successfully** (e.g., `get-configuration`, `list-webhooks`)

## Verification Commands

Run these commands to verify everything is working:

```bash
# Check service status
systemctl --user status mail-webhooks.service

# Check if backend image exists
podman image exists localhost/mail-webhooks-backend:latest && echo "Backend image exists"

# Test API health
curl -s http://127.0.0.1:20080/api/health

# Test configuration action
./actions/get-configuration/20read

# Check recent logs for errors
journalctl --user -u mail-webhooks.service -n 20 | grep -i error
```

## If Issues Persist

If you still encounter issues after applying the fix:

1. **Check the systemd service logs:**
   ```bash
   journalctl --user -u mail-webhooks.service -f
   ```

2. **Verify the backend image was built correctly:**
   ```bash
   podman images | grep mail-webhooks-backend
   ```

3. **Test the backend image directly:**
   ```bash
   podman run --rm -p 20080:20080 localhost/mail-webhooks-backend:latest
   ```

4. **Check environment variables:**
   ```bash
   cat environment | grep MAIL_WEBHOOKS_BACKEND_IMAGE
   ```

5. **Verify action script permissions:**
   ```bash
   ls -la actions/*/[0-9]*
   ```

## Common Troubleshooting

- **"Permission denied" errors**: Ensure all scripts have execute permissions (`chmod +x`)
- **"Image not found" errors**: Rebuild the backend image with the exact tag expected
- **"Line ending" issues**: Convert Windows CRLF to Unix LF using `sed -i 's/\r$//' filename`
- **"Service won't start"**: Check that the environment file contains the correct image reference

The automated fix script (`fix-server-permissions.sh`) handles all of these issues systematically.
