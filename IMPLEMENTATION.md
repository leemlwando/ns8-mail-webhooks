# NS8 Mail Webhooks Implementation Guide

## Overview
This document outlines the best practices and findings for implementing email address retrieval and webhook functionality within the NS8 ecosystem, specifically for the mail-webhooks module.

## Key Findings

### 1. Module Communication Best Practices

#### NS8 Standard Method
The proper way to communicate between NS8 modules is using the `agent.tasks.run()` method:

```python
import agent

result = agent.tasks.run(
    agent_id=f"module/{target_module_id}",
    action="action_name", 
    data={}
)
```

#### Alternative Methods (Not Recommended)
- Direct database access to other modules' SQLite files
- File system manipulation outside module boundaries
- Direct network calls to other services

### 2. Email Address Retrieval

#### Why This Approach?

Our email address fetching strategy was designed with several key principles:

1. **NS8 Ecosystem Compliance**: Uses `agent.tasks.run()` exclusively for inter-module communication, respecting NS8's security and modularity boundaries.

2. **Production Reliability**: Never returns dummy data; gracefully handles errors by returning empty arrays while providing detailed logging for troubleshooting.

3. **User Experience**: Provides comprehensive logging that appears in the NS8 UI through structured log levels, making debugging and monitoring transparent to administrators.

4. **Real-World Robustness**: Handles all ns8-mail address types and complex domain configurations, ensuring the webhook module works with any mail setup.

5. **Educational Value**: Logs address type breakdowns and processing steps to help administrators understand how their mail configuration translates to webhook-monitorable addresses.

#### Primary Source: ns8-mail Module
The ns8-mail module provides a standardized `list-addresses` action that returns:
- Domain-based addresses
- Wildcard addresses  
- User domain addresses (adduser domains)
- Group domain addresses (addgroup domains)

#### Response Structure
```json
{
    "adduser_domains": ["domain1.com", "domain2.com"],
    "addgroup_domains": ["domain1.com", "domain2.com"], 
    "addresses": [
        {
            "local": "username",
            "atype": "domain|wildcard|adduser|addgroup",
            "domain": "example.com",
            "destinations": [...],
            "description": "Optional description"
        }
    ]
}
```

### Technical Challenges Solved

#### 1. **Result Structure Navigation**
**Challenge**: NS8's `agent.tasks.run()` wraps action results in a structure where the actual data is in `result['output']`, not `result` directly.

**Solution**: Our implementation correctly extracts data from `result.get('output', {})` and provides fallback handling for missing or malformed responses.

#### 2. **Address Type Complexity**
**Challenge**: ns8-mail has four different address types with varying expansion rules, making it complex to generate the correct final email addresses.

**Solution**: Implemented type-specific processing logic that correctly expands adduser/addgroup addresses across their respective domain lists while maintaining domain and wildcard addresses as-is.

#### 3. **Deduplication Edge Cases**
**Challenge**: Multiple address types can generate identical final email addresses (e.g., a domain address `user@example.com` and an adduser address `user` with example.com in adduser_domains).

**Solution**: Applied Python's `set()` deduplication after all address expansion, with detailed logging to track when and why duplicates are removed.

#### 4. **Configuration Flexibility**
**Challenge**: Different NS8 installations might have mail modules with different IDs or multiple mail modules.

**Solution**: Uses environment variable `MAIL_MODULE_ID` with a sensible default ("mail1"), tests connectivity before attempting operations, and provides clear error messages for configuration issues.

#### 5. **UI Visibility for Debugging**
**Challenge**: Traditional Python logging doesn't appear in NS8's web UI, making troubleshooting difficult for administrators.

**Solution**: Uses NS8's structured logging levels (`agent.SD_*`) that appear in the UI, providing full visibility into address processing, type breakdowns, and any issues encountered.

### Production Deployment Considerations

#### Configuration
- Set `MAIL_MODULE_ID` environment variable if using a non-default mail module ID
- Ensure the mail-webhooks module has appropriate permissions to call the mail module
- Test connectivity with `api-cli run module/mail-webhooks1/list-email-addresses`

#### Monitoring
- Check NS8 logs for address type breakdowns and processing statistics
- Monitor for `SD_ERR` entries indicating mail module connectivity issues
- Watch for deduplication statistics to understand address overlap

#### Performance
- Address retrieval is on-demand, not cached
- For high-frequency webhook setups, consider implementing caching
- The current implementation prioritizes reliability over speed
1. **Domain addresses**: `local@domain`
2. **Wildcard addresses**: `local@*` (catch-all)
3. **Adduser addresses**: `local@{each_adduser_domain}`
4. **Addgroup addresses**: `local@{each_addgroup_domain}`

### 3. Implementation Strategy

#### Phase 1: Email Address Enumeration ✅
- Use `agent.tasks.run()` to call `mail1` module's `list-addresses` action
- Parse and normalize email addresses based on type
- Return clean list without duplicates
- Handle errors gracefully (return empty array, not dummy data)

#### Phase 2: Email Monitoring (Future)
- Use `reveal-master-credentials` action to get IMAP master credentials
- Implement IMAP polling for monitored addresses
- Use background services for real-time monitoring

#### Phase 3: Webhook Integration (Future)
- Store webhook configurations in module's own database
- Trigger webhooks based on email events
- Implement retry logic and error handling

## Email Address Fetching Logic: Deep Dive

### Address Type Education

Before diving into the implementation, it's crucial to understand the different types of email addresses that ns8-mail manages:

1. **Domain Addresses (`atype: "domain"`)**: 
   - Direct email addresses with specific domains
   - Example: `user@example.com`
   - These represent individual mailboxes or aliases with concrete domains

2. **Wildcard Addresses (`atype: "wildcard"`)**: 
   - Catch-all addresses that work with any domain
   - Example: `admin@*` 
   - These receive emails sent to that local part at ANY domain

3. **Adduser Addresses (`atype: "adduser"`)**: 
   - User accounts that are expanded across multiple "adduser domains"
   - Example: `john` becomes `john@domain1.com`, `john@domain2.com`
   - These represent real user accounts accessible via multiple domains

4. **Addgroup Addresses (`atype: "addgroup"`)**: 
   - Group accounts expanded across multiple "addgroup domains"
   - Example: `sales` becomes `sales@domain1.com`, `sales@domain2.com`
   - These represent mailing lists or group aliases

### Deduplication Strategy

Our implementation handles potential duplicates that can arise when:
- The same local part appears in multiple address types
- Adduser/addgroup domains overlap with domain addresses
- Multiple domains are configured for the same accounts

The deduplication process:
1. Collect all expanded email addresses
2. Use Python's `set()` to remove exact duplicates
3. Sort alphabetically for consistent ordering
4. Log the deduplication process for debugging

### Production-Grade Implementation

```python
#!/usr/bin/env python3

#
# Copyright (C) 2025 Lee M. Lwando
# SPDX-License-Identifier: GPL-3.0-or-later
#

import json
import sys
import os
import agent

def main():
    """Fetch email addresses from the mail module using proper NS8 agent communication"""
    
    try:
        # Call the mail module's list-addresses action using agent.tasks.run
        print(agent.SD_NOTICE + "Starting email address retrieval from mail module", file=sys.stderr)
        
        # Find the mail module ID - must be properly configured
        mail_module_id = find_mail_module()
        if not mail_module_id:
            print(agent.SD_ERR + "Mail module is not accessible - check cluster configuration and permissions", file=sys.stderr)
            json.dump([], fp=sys.stdout)
            return
        
        print(agent.SD_INFO + f"Found mail module: {mail_module_id}", file=sys.stderr)
        
        # Call the mail module using agent.tasks.run with proper user context
        print(agent.SD_DEBUG + f"Calling {mail_module_id}/list-addresses action with current user context", file=sys.stderr)
        
        # Use the current user's credentials and context
        result = agent.tasks.run(
            agent_id=f"module/{mail_module_id}",
            action="list-addresses",
            data={}
        )
        
        print(agent.SD_INFO + "Successfully received response from mail module", file=sys.stderr)
        print(agent.SD_DEBUG + f"Raw mail module response: {json.dumps(result, indent=2)}", file=sys.stderr)
        
        # Extract email addresses from the result (data is in result.output)
        email_addresses = extract_email_addresses(result.get('output', {}))
        
        print(agent.SD_NOTICE + f"Successfully extracted {len(email_addresses)} email addresses", file=sys.stderr)
        print(agent.SD_DEBUG + f"Final email addresses list: {json.dumps(email_addresses, indent=2)}", file=sys.stderr)
        
        # Return the email addresses as JSON
        json.dump(email_addresses, fp=sys.stdout)
        
    except Exception as e:
        print(agent.SD_ERR + f"Failed to fetch email addresses: {str(e)}", file=sys.stderr)
        # Return empty list on error - no dummy data
        json.dump([], fp=sys.stdout)

def find_mail_module():
    """Find the mail module ID in the cluster"""
    try:
        print(agent.SD_DEBUG + "Searching for mail module in cluster", file=sys.stderr)
        
        # Get the configured mail module ID - default to mail1
        mail_module_id = os.environ.get('MAIL_MODULE_ID', 'mail1')
        print(agent.SD_INFO + f"Using configured mail module: {mail_module_id}", file=sys.stderr)
        
        # Test if the mail module responds to a simple action
        print(agent.SD_DEBUG + f"Testing connection to mail module: {mail_module_id}", file=sys.stderr)
        
        result = agent.tasks.run(
            agent_id=f"module/{mail_module_id}",
            action="get-configuration",
            data={}
        )
        
        print(agent.SD_INFO + f"Successfully connected to mail module: {mail_module_id}", file=sys.stderr)
        print(agent.SD_DEBUG + f"Mail module connection test result: {json.dumps(result, indent=2)}", file=sys.stderr)
        
        return mail_module_id
        
    except Exception as e:
        print(agent.SD_ERR + f"Failed to connect to mail module '{mail_module_id}': {str(e)}", file=sys.stderr)
        print(agent.SD_ERR + "Please verify that the mail module is installed and accessible", file=sys.stderr)
        return None

def extract_email_addresses(result):
    """Extract email addresses from mail module result"""
    email_addresses = []
    
    if not result:
        print(agent.SD_WARNING + "No result received from mail module", file=sys.stderr)
        return []
    
    if 'addresses' not in result:
        print(agent.SD_WARNING + "No 'addresses' key found in mail module response", file=sys.stderr)
        print(agent.SD_DEBUG + f"Available keys in result: {list(result.keys())}", file=sys.stderr)
        print(agent.SD_DEBUG + f"Full result structure: {json.dumps(result, indent=2)}", file=sys.stderr)
        return []
    
    addresses_list = result['addresses']
    if not addresses_list:
        print(agent.SD_WARNING + "Addresses list is empty", file=sys.stderr)
        return []
    
    # Get domain lists for expansion
    adduser_domains = result.get('adduser_domains', [])
    addgroup_domains = result.get('addgroup_domains', [])
    
    print(agent.SD_INFO + f"Processing {len(addresses_list)} addresses from mail module", file=sys.stderr)
    print(agent.SD_DEBUG + f"Available adduser_domains: {json.dumps(adduser_domains, indent=2)}", file=sys.stderr)
    print(agent.SD_DEBUG + f"Available addgroup_domains: {json.dumps(addgroup_domains, indent=2)}", file=sys.stderr)
    
    # Track address types for educational logging
    type_counts = {'domain': 0, 'wildcard': 0, 'adduser': 0, 'addgroup': 0, 'unknown': 0}
    
    for addr in addresses_list:
        atype = addr.get('atype', 'unknown')
        local = addr.get('local', '')
        
        if not local:
            print(agent.SD_WARNING + f"Skipping address with empty local part: {json.dumps(addr)}", file=sys.stderr)
            continue
            
        type_counts[atype] = type_counts.get(atype, 0) + 1
        
        if atype == 'domain' and 'domain' in addr:
            email = f"{local}@{addr['domain']}"
            email_addresses.append(email)
            print(agent.SD_DEBUG + f"Added domain address: {email} (direct alias/mailbox)", file=sys.stderr)
            
        elif atype == 'wildcard':
            # For webhooks, wildcard addresses might be less useful, but include them
            email = f"{local}@*"
            email_addresses.append(email)
            print(agent.SD_DEBUG + f"Added wildcard address: {email} (catches all domains)", file=sys.stderr)
            
        elif atype == 'adduser':
            # User accounts - expand across all adduser domains
            if not adduser_domains:
                print(agent.SD_WARNING + f"Adduser address '{local}' found but no adduser_domains available", file=sys.stderr)
                continue
            for domain in adduser_domains:
                email = f"{local}@{domain}"
                email_addresses.append(email)
                print(agent.SD_DEBUG + f"Added adduser address: {email} (user account)", file=sys.stderr)
                
        elif atype == 'addgroup':
            # Group accounts - expand across all addgroup domains  
            if not addgroup_domains:
                print(agent.SD_DEBUG + f"Addgroup address '{local}' found but no addgroup_domains available", file=sys.stderr)
                continue
            for domain in addgroup_domains:
                email = f"{local}@{domain}"
                email_addresses.append(email)
                print(agent.SD_DEBUG + f"Added addgroup address: {email} (group account)", file=sys.stderr)
        else:
            print(agent.SD_WARNING + f"Unknown address type '{atype}' for {local}: {json.dumps(addr)}", file=sys.stderr)
    
    # Educational logging about address types found
    print(agent.SD_INFO + f"Address type breakdown: {json.dumps(type_counts)}", file=sys.stderr)
    
    # Remove duplicates and sort
    unique_addresses = sorted(list(set(email_addresses)))
    duplicates_removed = len(email_addresses) - len(unique_addresses)
    
    if duplicates_removed > 0:
        print(agent.SD_INFO + f"Removed {duplicates_removed} duplicate addresses during deduplication", file=sys.stderr)
        print(agent.SD_DEBUG + f"Original count: {len(email_addresses)}, Final count: {len(unique_addresses)}", file=sys.stderr)
        
    print(agent.SD_NOTICE + f"Final email list contains {len(unique_addresses)} unique addresses after processing {len(addresses_list)} address records", file=sys.stderr)
    
    return unique_addresses

if __name__ == "__main__":
    main()
```

### Key Implementation Features

#### 1. **Structured Logging with NS8 Standards**
Uses NS8's structured logging levels that appear in the UI:
- `agent.SD_NOTICE`: Important operations and results
- `agent.SD_INFO`: General information flow
- `agent.SD_DEBUG`: Detailed debugging information
- `agent.SD_WARNING`: Non-critical issues
- `agent.SD_ERR`: Critical errors

#### 2. **Robust Error Handling**
- Tests mail module connectivity before attempting address retrieval
- Handles missing mail modules gracefully
- Returns empty arrays on errors (never dummy data)
- Provides detailed error context in logs

#### 3. **Configuration-Driven Mail Module Discovery**
- Uses `MAIL_MODULE_ID` environment variable (defaults to "mail1")
- Tests connectivity to ensure the module is responsive
- Provides clear error messages for configuration issues

#### 4. **Address Type Processing and Education**
- Processes all four address types with different expansion logic
- Logs each address type's processing for educational purposes
- Handles edge cases (missing domains, empty local parts)
- Provides type breakdown statistics in logs

#### 5. **Production-Ready Result Extraction**
- Correctly extracts data from `result['output']` (not `result` directly)
- Validates response structure before processing
- Logs raw responses for debugging
- Handles missing or malformed data gracefully

#### 6. **Comprehensive Deduplication**
- Tracks original vs. final address counts
- Logs deduplication statistics
- Maintains deterministic ordering (sorted)
- Handles complex expansion scenarios gracefully

## Error Handling Best Practices

### 1. No Dummy Data in Production
Our implementation strictly adheres to the principle of never returning placeholder data:
- Always returns empty arrays (`[]`) on errors
- Never returns hardcoded email addresses like `user@example.com`
- Logs detailed error information for debugging while maintaining production integrity

### 2. Graceful Degradation
The implementation handles various failure scenarios:
- **Missing mail module**: Tests connectivity and provides clear error messages
- **Network/communication errors**: Catches exceptions and logs context
- **Malformed responses**: Validates response structure before processing
- **Permission issues**: Identifies and reports access problems clearly

### 3. Structured Logging for UI Visibility
Uses NS8's logging levels that appear in the web interface:
```python
print(agent.SD_NOTICE + "Important operation completed", file=sys.stderr)  # Shows in UI
print(agent.SD_INFO + "General information", file=sys.stderr)              # Shows in UI  
print(agent.SD_DEBUG + "Detailed debugging info", file=sys.stderr)         # Shows in UI
print(agent.SD_WARNING + "Non-critical issue", file=sys.stderr)            # Shows in UI
print(agent.SD_ERR + "Critical error occurred", file=sys.stderr)           # Shows in UI
```

### 4. Error Context Preservation
Every error includes sufficient context for troubleshooting:
- Module IDs and action names
- Raw response data (in debug mode)
- Step-by-step processing logs
- Type breakdowns and statistics

## UI Integration Benefits

### Real-Time Feedback for Administrators
Our implementation provides several benefits for the webhook configuration UI:

#### 1. **Transparent Address Loading**
- UI can display loading states while addresses are being fetched
- Real-time logs show the address discovery process
- Clear error messages appear immediately if mail module is unavailable

#### 2. **Educational Address Type Display**
The UI can leverage our address type logging to show administrators:
- How many domain vs. wildcard vs. user vs. group addresses were found
- Which domains are configured for user/group expansion  
- Why certain addresses appear multiple times before deduplication

#### 3. **Configuration Validation**
- Clear indicators when mail module connectivity fails
- Immediate feedback on permission or configuration issues
- Guidance for resolving common setup problems

#### 4. **Address Selection Intelligence**
With type information, the UI can:
- Group addresses by type for easier selection
- Highlight addresses that might receive high volumes (wildcards)
- Provide context about what each address type represents

#### 5. **Debugging Integration**
- Debug logs from address fetching appear directly in NS8's log viewer
- Administrators can troubleshoot webhook setup without terminal access
- Full traceability from UI action to address discovery to webhook configuration

### Recommended UI Design Patterns

#### Address Selection Interface
```
┌─ Email Addresses for Webhook Monitoring ─────────────────┐
│                                                          │
│ ✓ Direct Addresses (2 found)                            │
│   □ admin@example.com                                    │
│   □ support@example.com                                  │
│                                                          │
│ ✓ User Accounts (3 found, 2 domains)                    │
│   □ john@example.com, john@company.org                  │
│   □ jane@example.com, jane@company.org                  │
│                                                          │
│ ✓ Group Lists (1 found, 2 domains)                      │
│   □ sales@example.com, sales@company.org                │
│                                                          │
│ ⚠ Wildcard Addresses (1 found)                          │
│   □ catchall@* (all domains - high volume!)             │
│                                                          │
│ Status: ✓ Found 8 unique addresses from mail1           │
└──────────────────────────────────────────────────────────┘
```

#### Error State Display  
```
┌─ Email Addresses for Webhook Monitoring ─────────────────┐
│                                                          │
│ ⚠ Unable to load email addresses                        │
│                                                          │
│ Error: Mail module 'mail1' is not accessible            │
│                                                          │
│ Possible causes:                                         │
│ • Mail module is not installed                          │
│ • Insufficient permissions                               │
│ • Module configuration error                             │
│                                                          │
│ [View Logs] [Retry] [Configure Mail Module]             │
└──────────────────────────────────────────────────────────┘
```

## Testing and Validation

### 1. Module Installation
```bash
# Build module with UI (for full testing)
./build-images.sh

# Build without UI for action testing only  
./build-images.sh --skip-ui

# Add module to NS8
add-module mail-webhooks
```

### 2. Action Testing Methods

#### Direct Action Execution
```bash
# Test the action directly in the imageroot environment
runagent python3 /path/to/imageroot/actions/list-email-addresses/10list_email_addresses

# Test with debug output to see all logs
runagent python3 /path/to/imageroot/actions/list-email-addresses/10list_email_addresses 2>&1
```

#### NS8 API Testing
```bash
# Test via NS8 task system (recommended)
api-cli run module/mail-webhooks1/list-email-addresses

# Test with specific mail module configured
api-cli run module/mail-webhooks1/list-email-addresses --data '{"MAIL_MODULE_ID": "mail2"}'
```

#### UI Integration Testing  
```bash
# Test from the web interface
# Navigate to mail-webhooks module configuration
# Watch browser developer console for API calls
# Check NS8 logs for detailed processing information
```

### 3. Validation Checklist

#### Module Build Validation
- [ ] Module builds successfully without errors
- [ ] All dependencies are included in the container
- [ ] Action script has correct permissions (`chmod +x`)
- [ ] Action validation passes NS8 schema checks

#### Address Fetching Validation
- [ ] Action executes without Python syntax errors  
- [ ] Returns valid JSON array (even if empty)
- [ ] Handles missing mail module gracefully (returns `[]`)
- [ ] Logs appear in NS8 UI with appropriate levels
- [ ] No dummy data in production responses

#### Real Environment Testing
- [ ] Works with actual ns8-mail installation
- [ ] Correctly processes all address types found
- [ ] Deduplication logic handles overlapping addresses
- [ ] Configuration via `MAIL_MODULE_ID` works correctly
- [ ] Error states provide actionable information

#### Integration Validation  
- [ ] Mail module connectivity test passes
- [ ] Permission errors are handled gracefully
- [ ] UI can consume the JSON response format
- [ ] Logs provide sufficient debugging information
- [ ] Performance is acceptable for typical address counts

### 4. Common Testing Scenarios

#### Empty Mail Server
```json
Expected Response: []
Logs Should Show: "Addresses list is empty"
```

#### Mail Module Not Found
```json
Expected Response: []  
Logs Should Show: "Mail module is not accessible"
```

#### Permission Denied
```json
Expected Response: []
Logs Should Show: "Failed to connect to mail module"
```

#### Normal Operation
```json
Expected Response: ["user@example.com", "admin@company.org", ...]
Logs Should Show: Address type breakdowns and processing statistics
```

### 5. Performance Testing
```bash
# Measure response time for large address lists
time api-cli run module/mail-webhooks1/list-email-addresses

# Check memory usage during processing
api-cli run module/mail-webhooks1/list-email-addresses & 
ps aux | grep python3

# Test with multiple concurrent requests  
for i in {1..10}; do
    api-cli run module/mail-webhooks1/list-email-addresses &
done
wait
```

## Future Enhancements

### 1. IMAP Integration
- Retrieve master credentials: `agent.tasks.run("module/mail1", "reveal-master-credentials", {})`
- Implement IMAP polling for email monitoring
- Handle IMAP connection pooling and reconnection

### 2. Real-time Monitoring
- Background services for email polling
- Event-driven webhook triggers
- Queue management for webhook delivery

### 3. Advanced Features
- Email content extraction
- Attachment handling
- Message filtering and routing

## Security Considerations

### 1. Module Isolation
- Respect module boundaries
- Use official APIs only
- No direct file system access to other modules

### 2. Credential Management
- Use NS8's credential management
- Store sensitive data in module's own environment
- Use proper authentication for IMAP access

### 3. Permission Requirements
- `mailadm` role required for master credentials
- Proper role validation before sensitive operations

## Conclusion

The key to successful NS8 module development is:
1. **Respect modularity** - Use official APIs only
2. **Follow NS8 patterns** - Use agent.tasks.run() for inter-module communication
3. **Handle errors gracefully** - No dummy data, meaningful error messages
4. **Plan for scale** - Consider polling frequency and resource usage
5. **Security first** - Use proper authentication and authorization

This approach ensures our mail-webhooks module integrates seamlessly with the NS8 ecosystem while maintaining security and reliability standards.
