# NS8 Mail Webhooks Module

A powerful webhook system for NethServer 8 that monitors mailboxes and delivers real-time notifications and scheduled batch processing.

**Author:** Lee M. Lwando <leemlwando@gmail.com>  
**Package:** leemlwando/ns8-mail-webhooks

## Features

- **Real-time Webhooks**: Instant notifications for new messages, deletions, moves
- **Scheduled Processing**: Batch processing of mailboxes with configurable intervals
- **Multiple Authentication Methods**: Service accounts, user credentials, master user
- **Secure Delivery**: HMAC signatures, SSL verification, API key support
- **Message Actions**: Mark as read, delete, or move messages after processing
- **Comprehensive Logging**: Full audit trail and delivery tracking
- **High Performance**: Deno+Hono backend for efficient HTTP operations

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   NS8 Actions   │───▶│   Deno+Hono API  │───▶│   External      │
│   (Python)      │    │   (Webhook       │    │   Webhook       │
└─────────────────┘    │   Processing)    │    │   Endpoints     │
         │              └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   Mail Module   │    │   SQLite         │
│   Integration   │    │   Database       │
└─────────────────┘    └──────────────────┘
```

## Components

- **Python Event Bridge**: Integrates with NS8 mail modules via Redis events
- **Deno+Hono API Server**: High-performance webhook processing and delivery
- **SQLite Database**: Webhook configurations and delivery logs
- **Vue.js UI**: Modern web interface for configuration and monitoring

## Installation

1. Install from NS8 App Store or build from source
2. Configure mail module integration
3. Create webhook endpoints
4. Set up authentication credentials
5. Monitor delivery status

## Configuration

### Webhook Types

1. **Real-time Webhooks**: Triggered by mail events
2. **Scheduled Webhooks**: Batch processing at intervals

### Authentication Methods

1. **Service Account**: Dedicated mail service credentials
2. **User Credentials**: Individual user authentication
3. **Master User**: Administrative account with impersonation

### Message Actions

- Mark messages as read after successful delivery
- Delete processed messages
- Move messages to specific folders

## API Documentation

The module exposes a REST API for webhook management:

- `GET /api/webhooks` - List webhooks
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/:id` - Update webhook
- `DELETE /api/webhooks/:id` - Delete webhook
- `POST /api/webhooks/:id/test` - Test webhook delivery

## Security

- HMAC-SHA256 signatures for webhook verification
- SSL/TLS encryption for all HTTP requests
- API key authentication support
- Host allowlist for webhook endpoints
- Input validation and sanitization

## Monitoring

- Real-time service health monitoring
- Delivery success/failure tracking
- Performance metrics and statistics
- Comprehensive logging with retention policies

## License

GPL-3.0 License

## Support

For issues and support, please contact: leemlwando@gmail.com
