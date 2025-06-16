# NethServer 8 Mail Webhooks Module (`ns8-mail-webhooks`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NethServer 8](https://img.shields.io/badge/NethServer-8-blue.svg)](https://www.nethserver.org)

The NethServer 8 Mail Webhook module allows administrators to process emails from a designated mailbox and forward their contents to a configured webhook. It is designed to be a bridge between an email inbox and third-party services, such as an Applicant Tracking System (ATS), a CRM, or any custom automation workflow.

This module is fully modular and does not modify the core `ns8-mail` module. It interacts with the mail server using the standard IMAP protocol, ensuring stability and compatibility.

## Features

* **Scheduled Triggers**: Configure ongoing jobs to automatically process new, incoming emails from a mailbox in near-real-time.
* **One-Time Jobs**: Run an on-demand job to process all existing emails in a mailbox in a single batch. This is perfect for processing backlogs or for testing.
* **Flexible Configuration**: For each webhook, you can configure:
    * The destination Webhook URL.
    * An optional API Key for secure authentication.
    * The payload format: send the full `RAW` email or a structured `JSON` object.
* **User-Friendly Interface**: A simple, clean UI to manage all scheduled triggers and one-time jobs.
* **Modular Architecture**: Runs as a standalone module that interoperates with `ns8-mail` without direct modification, respecting the NethServer 8 design philosophy.

## Installation

This module will be available for installation from the NethServer 8 Software Center. Once installed, you will need to perform a one-time setup to begin processing emails.

## Setup and Configuration

The module works by "scraping" a designated mailbox via IMAP. For this to work, you must first configure a mailbox to receive the emails you want to process.

#### 1. Create a Processor Mailbox

Using the `ns8-mail` module's interface, create a dedicated mailbox that this module will connect to.
* **Example**: `webhook-processor@yourdomain.com`

#### 2. Configure Email Forwarding (for Scheduled Triggers)

For continuous, scheduled processing, you need to ensure a copy of the emails you want to process is delivered to the processor mailbox.

* Navigate to the `ns8-mail` module's UI.
* For each address you want to monitor (e.g., `hr@yourdomain.com`), create an alias or forwarding rule that delivers a copy to `webhook-processor@yourdomain.com` while still delivering to the original recipient.

#### 3. Configure the Mail Webhook Module

Navigate to the **Mail Webhooks** module in the NethServer 8 UI.

* **Scheduled Triggers**: Use this section to create ongoing jobs. You will map a monitored email address (e.g., `hr@yourdomain.com`) to a webhook URL. The module will process emails from the central processor mailbox and use the original recipient to determine which webhook to call.
* **Run a One-Time Job**: Use this section to process a mailbox immediately. You can select any mailbox on the system, and the module will process its contents.

#### 4. Provide Mailbox Credentials

The module's backend service needs the password for the processor mailbox to connect via IMAP. This is configured using environment variables for security.

For each mailbox the module needs to access, you must set an environment variable for the `ns8-mail-webhooks` container. The variable name is constructed as follows: `MAILBOX_PASSWORD_<email_address>`. The email address is sanitized by replacing `@` and `.` with `_`.

* **Example**: For the mailbox `webhook-processor@example.com`, the environment variable would be:
    ```
    MAILBOX_PASSWORD_webhook-processor_example_com="your-secret-password"
    ```

In a production environment, these variables should be managed securely through the cluster's configuration tools.

## Development

This module was developed using the `ns8-kickstart` template.

#### Build from Source

To build the container images from the source code, run the `build-images.sh` script:

```bash
./build-images.sh
```

#### Local Testing

To run the module in a local development environment, use the `test-module.sh` script. This will spin up a local NethServer instance and install the module.

```bash
./test-module.sh
```

## Author and License

This module was developed by:

**Lee M. Lwando**
- Email: leemlwando@gmail.com
- GitHub: [leemlwando](https://github.com/leemlwando)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Example:

    api-cli run module/kickstart1/configure-module --data '{}'

The above command will:
- start and configure the kickstart instance
- (describe configuration process)
- ...

Send a test HTTP request to the kickstart backend service:

    curl http://127.0.0.1/kickstart/

## Smarthost setting discovery

Some configuration settings, like the smarthost setup, are not part of the
`configure-module` action input: they are discovered by looking at some
Redis keys.  To ensure the module is always up-to-date with the
centralized [smarthost
setup](https://nethserver.github.io/ns8-core/core/smarthost/) every time
kickstart starts, the command `bin/discover-smarthost` runs and refreshes
the `state/smarthost.env` file with fresh values from Redis.

Furthermore if smarthost setup is changed when kickstart is already
running, the event handler `events/smarthost-changed/10reload_services`
restarts the main module service.

See also the `systemd/user/kickstart.service` file.

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

# ns8-mail-webooks
