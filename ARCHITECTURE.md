# NS8 Mail Webhook Module

A NethServer 8 module for automatically forwarding emails from IMAP mailboxes to HTTP webhooks.

## Architecture

### Backend (FastAPI + SQLite)

The backend is a Python FastAPI application that provides:

- **RESTful API** for managing triggers, jobs, and configuration
- **SQLite database** for storing triggers, jobs, and logs
- **IMAP client** for connecting to mail servers and fetching emails
- **Background worker** for scheduled job execution
- **Webhook processor** for sending emails to HTTP endpoints

#### Key Components

1. **`main.py`** - FastAPI application with REST endpoints
2. **`storage.py`** - SQLite database operations
3. **`imap_client.py`** - IMAP connection and email fetching
4. **`processor.py`** - Email processing and webhook delivery
5. **`worker.py`** - Background job scheduler and executor

#### API Endpoints

- `GET /api/health` - Health check
- `GET /api/stats` - Statistics
- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration
- `GET /api/mailboxes` - List available mailboxes
- `GET /api/triggers` - List scheduled triggers
- `POST /api/triggers` - Create trigger
- `PUT /api/triggers/{id}` - Update trigger
- `DELETE /api/triggers/{id}` - Delete trigger
- `GET /api/jobs` - List jobs
- `POST /api/jobs` - Create one-time job
- `GET /api/jobs/{id}` - Get job details
- `GET /api/logs` - Get logs

### Frontend (Vue.js + Carbon Design)

The frontend is a Vue.js application using IBM Carbon Design System:

- **Router-based navigation** (Status, Settings, Mail Webhooks, About)
- **Component-based architecture** for triggers and jobs
- **Real-time updates** via API polling
- **Form validation** and error handling
- **Responsive design** for mobile and desktop

#### Key Components

1. **`MailWebhooks.vue`** - Main page with tabbed interface
2. **`ScheduledTriggers.vue`** - Manage recurring email forwarding
3. **`OneTimeJob.vue`** - Run immediate email processing
4. **`Status.vue`** - Module status and health information
5. **`Settings.vue`** - Configuration management

### Deployment (Podman + Systemd)

The module uses containerized deployment:

- **Backend container** - Python FastAPI app with SQLite
- **UI container** - Static files served by NethServer
- **Systemd services** - Container lifecycle management
- **Traefik integration** - HTTP routing and SSL termination

#### Container Images

1. **mail-webhooks:latest** - Backend API server
2. **mail-webhooks** - UI static files and NethServer integration

## Configuration

### IMAP Settings

- **Host/Port** - IMAP server connection details
- **SSL/TLS** - Encryption settings
- **Authentication** - Username/password or OAuth

### Webhook Settings

- **Timeout** - HTTP request timeout
- **Retries** - Number of retry attempts
- **SSL Verification** - Certificate validation

### Performance Settings

- **Batch Size** - Emails processed per batch
- **Processing Delay** - Delay between batches
- **Connection Pool** - Maximum IMAP connections

## Usage

### Scheduled Triggers

1. Select source mailbox
2. Configure webhook URL and authentication
3. Set email processing options (mark read, delete, etc.)
4. Choose schedule (interval-based)
5. Enable the trigger

### One-Time Jobs

1. Select source mailbox
2. Configure webhook URL and authentication
3. Set processing options
4. Run immediately to process all existing emails

### Monitoring

- View job execution logs
- Monitor trigger status and statistics
- Check backend health and performance
- Export logs for troubleshooting

## Development

### Building

```bash
# Build backend and UI containers
./build-images.sh
```

### Testing

```bash
# Test backend API
./test-api.sh

# Run module tests
./test-module.sh
```

### Local Development

```bash
# Start backend
cd imageroot/pypkg
python -m mailwebhook.main

# Start UI development server
cd ui
npm install
npm run serve
```

## File Structure

```
ns8-mail-webhook/
├── imageroot/
│   ├── actions/          # NethServer actions
│   ├── pypkg/           # Python backend
│   │   └── mailwebhook/ # FastAPI application
│   └── systemd/         # Service definitions
├── ui/                  # Vue.js frontend
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page components
│   │   └── router/      # Navigation
│   └── public/          # Static assets
├── build-images.sh      # Container build script
├── test-api.sh         # API test script
└── README.md           # This file
```

## License

GPL-3.0-or-later
