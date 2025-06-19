# ns8-mail-webhooks

Mail Webhooks module for [NethServer 8](https://github.com/NethServer/ns8-core) that provides webhook triggers for incoming mail events through direct integration with the NS8 mail module.

## Features

### Core Functionality
- **Webhook Management**: Create, update, delete and test webhooks with full CRUD API
- **NS8 Mail Integration**: Direct integration with NS8 mail module - no external connections
- **Multiple Trigger Types**: Real-time and interval-based triggers with configurable intervals
- **Payload Formats**: Support for RAW and JSON payload types with message parsing
- **External MongoDB**: Uses external MongoDB instance (no self-hosted database)

### NS8-Only Mail Integration
- **Mail Module Discovery**: Automatic detection of NS8 mail server instances via agent communication
- **Service Communication**: Uses NS8 agent.tasks.run() for inter-module communication
- **Redis Integration**: Discovers mail services via NS8 Redis infrastructure
- **No External Connections**: Strictly NS8-internal - no IMAP, SMTP, or external mail server connections

### Message Processing
- **Advanced Filtering**: Sender, subject, and body pattern matching with regex support
- **Attachment Filtering**: Filter by attachment presence and message size
- **Mailbox Targeting**: Monitor specific mailboxes available through NS8 mail module
- **Message Parsing**: Email parsing through NS8 mail module API

### Background Services
- **Mail Monitor Service**: Dedicated background service for NS8 mail integration
- **Auto-Recovery**: Automatic service recovery with configurable retry logic
- **Performance Monitoring**: Response time tracking and execution logging

## Critical Requirements

⚠️ **NS8-Only Integration**: This module is designed exclusively for NethServer 8 environments and will NOT work with external mail servers.

### Strict NS8 Requirements

1. **NS8 Mail Module Required**: An active NS8 mail module (ns8-mail) must be installed and running
2. **No External Connections**: The module will not attempt connections to external IMAP, SMTP, or mail servers
3. **No Fallback Mechanisms**: If NS8 mail module is unavailable, the module will fail validation - no fallbacks
4. **Validation Enforced**: Configuration will fail if no NS8 mail module is detected

### Why NS8-Only?

- **Security**: Eliminates external network dependencies and potential security vulnerabilities
- **Reliability**: Ensures consistent operation within the NS8 ecosystem
- **Simplicity**: Reduces complexity by removing multiple integration paths
- **Compliance**: Aligns with NS8 architectural principles for module isolation

### NS8 Mail Module Integration

- **Direct Communication**: Uses `agent.tasks.run()` to call mail module actions
- **Service Discovery**: Discovers mail modules via Redis using `agent.list_service_providers()`
- **Real-time Data**: Gets current email addresses, domains, and user mailboxes
- **Actions Used**: `list-addresses`, `list-user-mailboxes`, `list-domains`

### Requirements

- **NS8 Environment**: This module requires a running NS8 cluster
- **Mail Module**: An active NS8 mail module (ns8-mail) must be installed
- **No External Connections**: Does not attempt connections to external mail servers

### Email Address Discovery

The system compiles email addresses from:
- Configured mail addresses (aliases, forwards)
- User mailboxes on domains with `addusers=true`
- Public mailboxes and shared addresses
- Custom address configurations

### Testing Integration

Use the test action to verify mail integration:

```bash
# Test mail module connectivity and discovery
runagent test-mail-integration

# Get available email addresses
runagent get-email-addresses
```

If no NS8 mail module is found, the module will fail validation and require proper mail integration.

See `MAIL_INTEGRATION.md` for detailed technical documentation.

## Install

Instantiate the module with:

    add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "mail-webhooks1", "image_name": "ns8-mail-webhooks", "image_url": "ghcr.io/leemlwando/ns8-mail-webhooks:latest"}

## Configure

Let's assume that the mail-webhooks instance is named `mail-webhooks1`.

Launch `configure-module`, by setting the following parameters:
- `mongodb_url`: MongoDB connection URL (required)
- `mail_server_uuid`: UUID of the mail server to integrate with (optional)
- `webhooks_collection`: MongoDB collection name for webhooks (default: "webhooks")
- `events_collection`: MongoDB collection name for mail events (default: "events")  
- `settings_collection`: MongoDB collection name for settings (default: "settings")
- `triggers_collection`: MongoDB collection name for triggers (default: "triggers")
- `logs_collection`: MongoDB collection name for logs (default: "logs")
- `http2https`: enable or disable HTTP to HTTPS redirection (true/false)
- `lets_encrypt`: enable or disable Let's Encrypt certificate (true/false)

Example:

```bash
api-cli run configure-module --agent module/mail-webhooks1 --data - <<EOF
{
  "mongodb_url": "mongodb://user:password@mongo.example.com:27017/mailwebhooks",
  "mail_server_uuid": "24c52316-5af5-4b4d-8b0f-734f9ee9c1d9",
  "webhooks_collection": "my_webhooks",
  "events_collection": "my_events",
  "triggers_collection": "my_triggers",
  "logs_collection": "my_logs",
  "http2https": true,
  "lets_encrypt": false
}
EOF
```

### Collection Names

The module allows you to customize the MongoDB collection names used for data storage. This is useful when:
- Multiple instances need to share the same MongoDB database
- You want to organize data with custom naming conventions
- Integration with existing systems requires specific collection names

All collection names must follow MongoDB naming rules:
- Start with a letter or underscore
- Contain only letters, numbers, and underscores
- Cannot be empty

If collection names are not specified, the module uses these defaults:
- `webhooks` - for webhook configurations
- `events` - for mail events and webhook execution logs
- `settings` - for module settings
- `triggers` - for trigger scheduling information
- `logs` - for execution logs and debugging information

The above command will:
- Configure the module to use the specified MongoDB instance
- Set up integration with the specified mail server  
- Use custom collection names for data organization
- Configure Traefik routing for the web interface

## Get the configuration

You can retrieve the configuration with:

```bash
api-cli run get-configuration --agent module/mail-webhooks1 --data null | jq
```

## API Endpoints

The module provides a REST API for webhook management:

- `GET /health` - Service health check
- `GET /api/webhooks` - List all webhooks
- `POST /api/webhooks` - Create new webhook
- `GET /api/webhooks/{id}` - Get webhook details
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## Uninstall

To uninstall the instance:

    remove-module --no-preserve mail-webhooks1

## Development Status

This module is currently in development. Phase 1 (Backend Foundation) is complete with a FastAPI-based REST API for webhook management, including support for custom MongoDB collection names.

## Deployment & Troubleshooting

### Server-Side Issues

If you encounter permission errors or image-related issues after deployment, use the provided troubleshooting tools:

1. **Quick Fix (Recommended)**:
   ```bash
   # Copy the fix script to your server
   scp fix-server-permissions.sh root@your-server:/tmp/
   
   # SSH to server and run as the module user
   ssh root@your-server
   su - mail-webhooks1  # Replace with your module instance name
   cd ~/.config/containers/systemd
   cp /tmp/fix-server-permissions.sh .
   chmod +x fix-server-permissions.sh
   ./fix-server-permissions.sh
   ```

2. **Verification**:
   ```bash
   # Copy and run the verification script
   scp verify-module.sh root@your-server:/tmp/
   su - mail-webhooks1
   cd ~/.config/containers/systemd
   cp /tmp/verify-module.sh .
   chmod +x verify-module.sh
   ./verify-module.sh
   ```

3. **Manual Troubleshooting**:
   See `SERVER_TROUBLESHOOTING.md` for detailed manual fix procedures.

### Common Issues

- **Permission denied errors**: Action scripts need execute permissions
- **Image not found errors**: Backend image must be built locally, not pulled from registry
- **Service startup failures**: Environment variables and image configuration must match
- **Line ending issues**: Scripts must use Unix (LF) line endings, not Windows (CRLF)

### Service Status

Check service status and logs:
```bash
systemctl --user status mail-webhooks.service
journalctl --user -u mail-webhooks.service -f
curl -s http://127.0.0.1:20080/api/health
```

## Testing

Test the module using the `test-module.sh` script:

    ./test-module.sh <NODE_ADDR> ghcr.io/leemlwando/ns8-mail-webhooks:latest

The tests are made using [Robot Framework](https://robotframework.org/)

Test collection configuration:

    python test-collection-config.py

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/continuous.html#github-setup) to your repository
- add your repository to [hosted.weblate.org]((https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
