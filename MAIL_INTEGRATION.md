# NS8 Mail Integration Analysis

## Overview

This document outlines our analysis of the NS8 mail module (ns8-mail) and integration approaches for the mail-webhooks module.

## NS8 Mail Module Structure

### Key Actions Available

1. **`list-addresses`** - Returns all mail addresses handled by the server
   - Output includes addresses with types: `domain`, `adduser`, `wildcard`
   - Provides destination information and descriptions
   - Includes internal/external flags

2. **`list-user-mailboxes`** - Returns user mailbox information
   - User accounts, quota information, enabled status
   - Forward rules and spam retention settings

3. **`list-domains`** - Returns configured mail domains
   - Domain names with `addusers`/`addgroups` flags
   - Catchall settings and descriptions

4. **`list-public-mailboxes`** - Returns public/shared mailboxes

### Mail Module Data Structures

#### Address Format (from list-addresses)
```json
{
  "local": "username",
  "destinations": [
    {
      "dtype": "user|public|external|group",
      "name": "destination",
      "ui_name": "Display Name"
    }
  ],
  "atype": "domain|adduser|wildcard",
  "domain": "example.com",
  "description": "Description",
  "internal": false,
  "delete_forbidden": false
}
```

#### User Mailbox Format (from list-user-mailboxes)
```json
{
  "user": "username",
  "enabled": true,
  "quota": {
    "limit": 1024,
    "value": 256,
    "percent": 25,
    "custom": false
  },
  "forward": {
    "destinations": [],
    "keepcopy": true
  },
  "spam_retention": {
    "custom": false,
    "value": 15
  }
}
```

#### Domain Format (from list-domains)
```json
{
  "domain": "example.com",
  "addusers": true,
  "addgroups": false,
  "catchall": null,
  "bccaddr": "",
  "description": "Main domain"
}
```

# NS8 Mail Integration Analysis

## Overview

This document outlines the NS8-only mail integration approach for the mail-webhooks module. The module is designed exclusively for NS8 environments and does not support external mail server connections.

## Design Principles

- **NS8 Native**: Built specifically for NS8 cluster environments
- **No External Dependencies**: Does not connect to external mail servers
- **Direct Integration**: Uses NS8's inter-module communication patterns
- **Fail Fast**: Requires active NS8 mail module, fails validation if not available

## Integration Approach

### Single Source: NS8 Mail Module

Uses NS8's `agent.tasks.run()` to call mail module actions directly:

```python
import agent.tasks

# Get email addresses
addresses_result = agent.tasks.run(
    agent_id='mail1@node',
    action='list-addresses',
    data={}
)

# Get user mailboxes  
mailboxes_result = agent.tasks.run(
    agent_id='mail1@node',
    action='list-user-mailboxes',
    data={}
)

# Get domains
domains_result = agent.tasks.run(
    agent_id='mail1@node',
    action='list-domains',
    data={}
)
```

**Advantages:**
- Direct access to authoritative mail data
- Real-time information
- Uses NS8's standard inter-module communication
- No external network dependencies
- Secure, authenticated access

### Redis Service Discovery

Uses NS8's Redis infrastructure to discover mail services:

```python
import agent

# Method 1: Use NS8 service provider discovery
with agent.redis_connect() as rdb:
    for service in agent.list_service_providers(rdb, 'imap', 'tcp'):
        module_id = service.get('module_id')
        if module_id and module_id.startswith('mail'):
            # Found mail module
            break

# Method 2: Direct Redis key pattern matching
with agent.redis_connect() as rdb:
    keys = rdb.keys('module/mail*/srv/tcp/imap')
    for key in keys:
        module_id = key.split('/')[1]  # Extract mail1, mail2, etc.
```

**Advantages:**
- Automatic discovery of mail modules
- Works with multiple mail instances
- Uses NS8's standard service discovery

## Implementation Strategy

### Single Source Approach

The implementation enforces NS8-only integration:

1. **Discover mail module** via Redis service discovery
2. **Call mail module actions** using `agent.tasks.run()`
3. **Fail validation** if no mail module is available
4. **Return structured data** for UI consumption

### Email Address Compilation

From the mail module data, we compile email addresses as:

```python
email_addresses = []

# From addresses (domain type)
for addr in addresses_result['addresses']:
    if addr['atype'] == 'domain':
        email = f"{addr['local']}@{addr['domain']}"
        email_addresses.append({
            'email': email,
            'type': 'address',
            'description': addr.get('description', ''),
            'internal': addr.get('internal', False)
        })

# From user mailboxes + adduser domains
for mailbox in mailboxes_result['user_mailboxes']:
    for domain in domains_result:
        if domain['addusers']:
            email = f"{mailbox['user']}@{domain['domain']}"
            email_addresses.append({
                'email': email,
                'type': 'mailbox',
                'description': f"User mailbox: {mailbox['user']}",
                'enabled': mailbox.get('enabled', True)
            })
```

## Current Implementation

### get-email-addresses Action

Located: `imageroot/actions/get-email-addresses/10list`

**Features:**
- Discovers mail module ID via Redis service discovery
- Calls mail module actions using `agent.tasks.run()`
- Processes addresses, mailboxes, and domains
- **Fails validation if no mail module found** (NS8-only requirement)
- Returns structured JSON with mail module information

**Output Format:**
```json
{
  "success": true,
  "source": "ns8-mail",
  "mail_module_id": "mail1",
  "email_addresses": [
    {
      "email": "user@example.com",
      "type": "address|user|mailbox",
      "description": "Description",
      "internal": false,
      "enabled": true
    }
  ]
}
```

**Error Handling:**
- Returns validation error if no mail module is found
- Sets agent status to 'validation-failed'
- Provides clear error messages for debugging

### NS8 Mail Discovery

Located: `imageroot/api/mail_discovery.py`

**Features:**
- Uses `agent.list_service_providers()` for service discovery
- Falls back to direct Redis key pattern matching
- Returns mail module metadata (ID, host, ports, etc.)
- **No external connections** - NS8 agent framework only

### Integration Testing

Created test action: `imageroot/actions/test-mail-integration/10test`

**Tests:**
1. Redis connectivity via NS8 agent
2. `agent.tasks` module availability
3. Mail module discovery
4. Mail module action calls
5. End-to-end integration validation

## Best Practices

### Error Handling
- **Strict Validation**: Fail fast if NS8 mail module is not available
- **Clear Error Messages**: Provide actionable error information
- **Agent Status**: Use NS8 agent status system for validation errors

### Service Discovery
- **Prefer NS8 APIs**: Use `agent.list_service_providers()` when possible
- **Redis Fallback**: Use direct Redis key patterns as secondary method
- **No Assumptions**: Don't assume mail module IDs or configurations

### Data Processing
- **Filter System Addresses**: Remove vmail and other system accounts
- **Handle Duplicates**: Prevent duplicate email addresses in results
- **Respect Configuration**: Honor mail module's internal flags and settings
- **User Enablement**: Consider user account enabled/disabled status

### Security
- **Agent Framework Only**: Use NS8 agent Redis connections exclusively
- **No External Access**: Never attempt external mail server connections
- **Validate Responses**: Validate all data from mail module responses
- **Fail Securely**: Default to secure failure modes

## Conclusion

The NS8-only mail integration approach provides a secure, reliable, and maintainable solution for mail-based webhook functionality. By enforcing NS8 environment requirements and failing validation when proper integration is not available, the module ensures consistent behavior and prevents configuration issues.

This approach aligns with NS8's architecture and provides a solid foundation for enterprise mail webhook functionality within the NS8 ecosystem.
