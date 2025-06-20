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

#### Address Types Processing
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

## Code Implementation

### Current Working Implementation

```python
#!/usr/bin/env python3
import json
import sys
import agent

def main():
    try:
        # Find mail module
        mail_module_id = find_mail_module()
        if not mail_module_id:
            print("ERROR: No mail module found", file=sys.stderr)
            json.dump([], fp=sys.stdout)
            return
        
        # Call mail module
        result = agent.tasks.run(
            agent_id=f"module/{mail_module_id}",
            action="list-addresses",
            data={}
        )
        
        # Extract and return email addresses
        email_addresses = extract_email_addresses(result)
        json.dump(email_addresses, fp=sys.stdout)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        json.dump([], fp=sys.stdout)

def find_mail_module():
    try:
        modules = agent.list_modules()
        mail_modules = [m for m in modules if m.startswith('mail')]
        return mail_modules[0] if mail_modules else None
    except Exception:
        return None

def extract_email_addresses(result):
    email_addresses = []
    
    if not result or 'addresses' not in result:
        return []
    
    for addr in result['addresses']:
        if addr.get('atype') == 'domain' and 'domain' in addr:
            email_addresses.append(f"{addr['local']}@{addr['domain']}")
        elif addr.get('atype') == 'wildcard':
            email_addresses.append(f"{addr['local']}@*")
        elif addr.get('atype') == 'adduser':
            for domain in result.get('adduser_domains', []):
                email_addresses.append(f"{addr['local']}@{domain}")
        elif addr.get('atype') == 'addgroup':
            for domain in result.get('addgroup_domains', []):
                email_addresses.append(f"{addr['local']}@{domain}")
    
    return sorted(list(set(email_addresses)))

if __name__ == "__main__":
    main()
```

## Error Handling Best Practices

### 1. No Dummy Data in Production
- Always return empty arrays on errors
- Never return placeholder/dummy data
- Log errors to stderr for debugging

### 2. Graceful Degradation
- Handle missing mail module gracefully
- Handle network/communication errors
- Provide meaningful error messages in logs

### 3. Verbose Logging
- Log major steps to stderr for debugging
- Include module IDs and response sizes
- Log errors with sufficient context

## Testing and Validation

### 1. Module Installation
```bash
# Build without UI for testing
./build-images.sh --skip-ui

# Add module to NS8
add-module mail-webhooks
```

### 2. Action Testing
```bash
# Test the action directly
runagent python3 /path/to/action

# Test via NS8 task system
api-cli run module/mail-webhooks13/list-email-addresses
```

### 3. Validation Checklist
- [ ] Module builds successfully
- [ ] Action executes without Python errors
- [ ] Returns valid JSON array
- [ ] Handles missing mail module gracefully
- [ ] Logs errors appropriately
- [ ] No dummy data in production responses

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
