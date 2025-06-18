# Fix for NS8 Mail Webhooks Installation Failure

## Issue
The `create-module` action is failing during module installation, causing an assertion error:
```
Assertion failed
File "/var/lib/nethserver/cluster/actions/add-module/50update", line 196
agent.assert_exp(create_module_result['exit_code'] == 0)
```

## Root Cause
Action scripts in the container image don't have executable permissions, causing permission denied errors when NS8 tries to run them.

## Quick Fix (Server-Side)

### Step 1: Clean up failed installation
```bash
# Find and remove any failed module instances
remove-module --no-preserve mail-webhooks1  # Replace with actual instance name
```

### Step 2: Update to latest code
```bash
cd /path/to/ns8-mail-webhooks
git checkout dev-v2
git pull origin dev-v2
```

### Step 3: Rebuild the module with fixed permissions
```bash
./build-images.sh
```

### Step 4: Reinstall the module
```bash
add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1
```

## Alternative: Manual Permission Fix

If you have a partially installed module, you can try to fix it manually:

```bash
# Find the module directory
MODULE_DIR=$(find /home -name "ns8-mail-webhooks*" -type d | tail -1)
MODULE_USER=$(basename "$MODULE_DIR")

# Fix permissions
sudo -u "$MODULE_USER" find "$MODULE_DIR/.config/actions" -name "[0-9]*" -type f -exec chmod +x {} \;
sudo -u "$MODULE_USER" find "$MODULE_DIR/.config/bin" -type f -exec chmod +x {} \;

# Try to complete the installation
api-cli run create-module --agent "module/$MODULE_USER" --data '{"images": []}'
```

## Diagnostic Script

Use the provided troubleshooting script:
```bash
# Copy to server and run
scp troubleshoot-installation.sh root@your-server:/tmp/
ssh root@your-server
chmod +x /tmp/troubleshoot-installation.sh
/tmp/troubleshoot-installation.sh
```

## Prevention

The latest code includes:
- ✅ `01fix_permissions` script that runs first in create-module
- ✅ Updated build script that ensures all scripts are executable  
- ✅ Comprehensive permission fixes in all deployment scripts

## Verification

After successful installation:
```bash
# Check module status
api-cli run get-status --agent module/mail-webhooks1 --data null

# Check service status  
systemctl --user status mail-webhooks.service

# Test API
curl -s http://127.0.0.1:20080/api/health
```

## Next Steps

1. Remove any failed installations
2. Pull latest code with permission fixes
3. Rebuild and reinstall the module
4. The module should now install successfully without assertion errors
