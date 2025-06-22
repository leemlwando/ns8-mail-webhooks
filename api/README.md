# NS8 Mail Webhooks API

FastAPI-based REST API for managing email webhooks and scheduled jobs.

## Features

- **Webhook Management**: CRUD operations for email webhooks
- **Scheduled Jobs**: APScheduler integration with MongoDB job store
- **Real-time Triggers**: IMAP IDLE monitoring for instant email processing
- **Email Processing**: Send webhook notifications when emails are received
- **Logging**: Comprehensive logging of webhook executions and errors
- **Statistics**: Dashboard-ready webhook statistics

## Architecture

- **FastAPI**: Modern, fast web framework for building APIs
- **APScheduler**: Advanced Python Scheduler for job management
- **PyMongo/Motor**: Async MongoDB driver for data persistence
- **IMAP IDLE**: Real-time email monitoring (simplified polling implementation)
- **Webhooks**: HTTP POST notifications to external services

## Master Credentials

This API operates with master credentials within the NS8 secure cluster, providing:
- Centralized security management
- Simplified authentication logic
- Enhanced security through cluster isolation
- Administrative access to all configured email accounts

## API Endpoints

### Webhooks
- `POST /api/webhooks` - Create webhook
- `GET /api/webhooks` - List webhooks (with pagination and filtering)
- `GET /api/webhooks/{id}` - Get webhook details
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/toggle` - Enable/disable webhook
- `POST /api/webhooks/{id}/test` - Test webhook with sample data

### Jobs
- `GET /api/jobs` - List scheduled jobs
- `GET /api/jobs/{id}` - Get job details

### Logs
- `GET /api/logs` - List execution logs

### Statistics
- `GET /api/stats` - Get webhook statistics

### Health
- `GET /health` - Health check endpoint

## Configuration

The API uses environment variables for configuration:
- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DATABASE`: Database name
- `COLLECTION_WEBHOOKS`: Webhooks collection name
- `COLLECTION_JOBS`: Jobs collection name
- `COLLECTION_LOGS`: Logs collection name

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Docker Build

```bash
# Build API container
docker build -t ns8-mail-webhooks-api .

# Run container
docker run -p 8000:8000 \
  -e MONGODB_URL="mongodb://localhost:27017" \
  -e MONGODB_DATABASE="webhooks" \
  ns8-mail-webhooks-api
```

## Integration

The API integrates with:
- NS8 cluster configuration for database settings
- External webhook endpoints for notifications
- Email servers via IMAP for real-time monitoring
- Frontend UI for webhook management