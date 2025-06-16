# ns8-mail-webhooks

Mail webhooks module for NethServer 8, developed by Lee M. Lwando.

## Overview

This module provides webhook functionality for mail events in NethServer 8.

## Install

Instantiate the module with:

    add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "ns8-mail-webhooks1", "image_name": "ns8-mail-webhooks", "image_url": "ghcr.io/leemlwando/ns8-mail-webhooks:latest"}

## Configure

Let's assume that the ns8-mail-webhooks instance is named `ns8-mail-webhooks1`.

Launch `configure-module`, by setting the following parameters:
- `<MODULE_PARAM1_NAME>`: <MODULE_PARAM1_DESCRIPTION>
- `<MODULE_PARAM2_NAME>`: <MODULE_PARAM2_DESCRIPTION>
- ...

Example:

    api-cli run module/ns8-mail-webhooks1/configure-module --data '{}'

The above command will:
- start and configure the ns8-mail-webhooks instance
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

    remove-module --no-preserve ns8-mail-webhooks1

## Testing

Test the module using the `test-module.sh` script:


    ./test-module.sh <NODE_ADDR> ghcr.io/leemlwando/ns8-mail-webhooks:latest

The tests are made using [Robot Framework](https://robotframework.org/)

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/continuous.html#github-setup) to your repository
- add your repository to [hosted.weblate.org]((https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
