# ns8-mail-webhooks

Mail Webhooks module for [NethServer 8](https://github.com/NethServer/ns8-core) that provides webhook triggers for incoming mail events.

## Features

- **Webhook Management**: Create, update, delete and test webhooks
- **Multiple Trigger Types**: Real-time and interval-based triggers
- **Payload Formats**: Support for RAW and JSON payload types
- **Mail Integration**: Integrates with ns8-mail module for mailbox access
- **External MongoDB**: Uses external MongoDB instance (no self-hosted database)

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
