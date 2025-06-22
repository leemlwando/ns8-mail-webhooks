# ns8-mail-webhooks

A NethServer 8 module for managing mail webhooks. This module allows you to configure webhooks that are triggered when emails are received, providing integration with external services and APIs.

## Features

- **MongoDB Integration**: Store webhook configurations and email data in MongoDB
- **Flexible Webhook Configuration**: Support for both real-time and scheduled webhook triggers
- **Multiple Payload Types**: Send webhooks as JSON or raw format
- **Post-processing Actions**: Mark emails as read or delete them after webhook execution
- **Web UI**: User-friendly interface for managing webhook configurations
- **Email Domain Integration**: Automatically discover available email domains from NS8 mail server

## Install

Instantiate the module with:

    add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "mail-webhooks1", "image_name": "ns8-mail-webhooks", "image_url": "ghcr.io/leemlwando/ns8-mail-webhooks:latest"}

## Configure

Let's assume that the mail-webhooks instance is named `mail-webhooks1`.

### Settings Configuration

Configure the module with the following parameters:
- `mongodb_url`: MongoDB connection URL (e.g., `mongodb://localhost:27017/mailwebhooks`)
- `webhooks_collection`: Collection name for storing webhook configurations (default: `webhooks`)
- `emails_collection`: Collection name for storing email data (default: `emails`)
- `logs_collection`: Collection name for storing execution logs (default: `logs`)

Example:
```bash
api-cli run configure-module --agent module/mail-webhooks1 --data '{"mongodb_url":"mongodb://localhost:27017/mailwebhooks","webhooks_collection":"webhooks","emails_collection":"emails","logs_collection":"logs"}'
```

### Webhook Configuration

Use the web interface to configure webhooks with the following options:

- **Name**: Descriptive name for the webhook
- **URL**: Target endpoint for webhook delivery
- **API Key**: Optional authentication key
- **Email Address**: Email address to monitor (selected from available domains)
- **Payload Type**: JSON or Raw format
- **Post Action**: None, Mark as Read, or Delete email after processing
- **Trigger Type**: Real-time or Scheduled execution
- **Schedule Interval**: For scheduled webhooks (5min, 15min, 30min, 1hour, 6hours, 12hours, 24hours)
- **Enabled**: Toggle webhook on/off

Example:

    api-cli run module/mail-webhooks1/configure-module --data '{}'

The above command will:
- start and configure the mail-webhooks instance
- (describe configuration process)
- ...

Send a test HTTP request to the mail-webhooks backend service:

    curl http://127.0.0.1/mail-webhooks/

## Smarthost setting discovery

Some configuration settings, like the smarthost setup, are not part of the
`configure-module` action input: they are discovered by looking at some
Redis keys.  To ensure the module is always up-to-date with the
centralized [smarthost
setup](https://nethserver.github.io/ns8-core/core/smarthost/) every time
mail-webhooks starts, the command `bin/discover-smarthost` runs and refreshes
the `state/smarthost.env` file with fresh values from Redis.

Furthermore if smarthost setup is changed when mail-webhooks is already
running, the event handler `events/smarthost-changed/10reload_services`
restarts the main module service.

See also the `systemd/user/mail-webhooks.service` file.

This setting discovery is just an example to understand how the module is
expected to work: it can be rewritten or discarded completely.

## Uninstall

To uninstall the instance:

    remove-module --no-preserve kickstart1

## Testing

Test the module using the `test-module.sh` script:


    ./test-module.sh <NODE_ADDR> ghcr.io/nethserver/kickstart:latest

The tests are made using [Robot Framework](https://robotframework.org/)

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/continuous.html#github-setup) to your repository
- add your repository to [hosted.weblate.org]((https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
