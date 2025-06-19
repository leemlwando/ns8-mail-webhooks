# NS8-Only Mail Integration Policy

## Overview

The mail-webhooks module for NethServer 8 has been designed with a **strict NS8-only integration policy**. This document outlines the architectural decisions and implementation details that enforce this policy.

## Policy Statement

🚫 **NO EXTERNAL MAIL SERVERS**  
🚫 **NO FALLBACK MECHANISMS**  
🚫 **NO IMAP/SMTP CONNECTIONS**  
✅ **NS8 MAIL MODULE ONLY**

## Implementation Details

### Validation Layer
- **03mail_module_validation**: Validates NS8 mail module availability during configuration
- **Fails Fast**: Configuration fails immediately if no NS8 mail module is found
- **No Bypass**: No configuration options to bypass this requirement

### Mail Discovery
- **NS8 Agent Integration**: Uses `agent.tasks.run()` for inter-module communication
- **Redis Service Discovery**: Discovers mail services via NS8 Redis infrastructure  
- **No External Redis**: Removed all external Redis connection capabilities

### Backend Services
- **mail_monitor.py**: Rewritten to use only NS8 mail module APIs
- **mail_discovery.py**: NS8-only service discovery
- **Removed Files**: `imap_integration.py` and all IMAP-related code eliminated

### Error Handling
- **Clear Error Messages**: UI displays specific errors when NS8 mail module is unavailable
- **No Silent Failures**: All mail integration failures are explicit and visible
- **Validation Feedback**: Users are clearly informed of NS8-only requirements

## Files Modified for NS8-Only Policy

### Removed/Cleaned
- `imageroot/api/imap_integration.py` (deleted)
- All IMAP and external mail references from `mail_monitor.py`
- Fallback logic from `get-email-addresses` action
- External mail server environment variables

### Added/Enhanced
- `imageroot/actions/configure-module/03mail_module_validation`
- NS8-only error messages in translation files
- Strict validation schemas allowing only "ns8-mail" source
- Updated documentation emphasizing NS8-only approach

### Configuration
- **MongoDB Only**: External MongoDB for data storage (required)
- **NS8 Mail Module**: Must be available for email address discovery
- **No IMAP Config**: No IMAP server configuration options
- **No External Credentials**: No external mail server authentication

## Testing NS8-Only Integration

```bash
# Test mail module discovery (should find NS8 mail modules)
runagent test-mail-integration

# Test email address discovery (should use NS8 mail module)
runagent get-email-addresses

# Configuration (should fail without NS8 mail module)
configure-module '{"mongodb_url": "mongodb://...", "hostname": "..."}'
```

## Expected Behavior

### With NS8 Mail Module
- ✅ Configuration succeeds
- ✅ Email addresses discovered from NS8 mail module
- ✅ Webhooks can be created for discovered addresses
- ✅ Integration works seamlessly

### Without NS8 Mail Module  
- ❌ Configuration fails at validation step
- ❌ Clear error message: "NS8 mail module is required"
- ❌ No fallback or bypass options
- ❌ Module refuses to start

## Architecture Benefits

1. **Security**: No external network connections reduce attack surface
2. **Reliability**: Single integration point eliminates configuration complexity
3. **Maintainability**: Simplified codebase with single responsibility
4. **NS8 Compliance**: Follows NS8 architectural patterns for module isolation
5. **Predictable Behavior**: No conditional logic based on external availability

## Support and Troubleshooting

If the module fails to start:

1. **Check NS8 Mail Module**: Ensure ns8-mail is installed and running
2. **Verify Service Discovery**: Test with `runagent test-mail-integration`
3. **Check Logs**: Review module logs for specific NS8 integration errors
4. **No External Options**: Do not attempt to configure external mail servers

This policy ensures the module operates reliably and securely within the NS8 ecosystem while maintaining clear, predictable behavior for administrators.
