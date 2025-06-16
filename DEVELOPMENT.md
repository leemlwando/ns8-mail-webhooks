# NS8 Mail Webhooks - Development Guide

This guide helps you set up a complete development environment for the NethServer 8 Mail Webhooks module using VS Code Dev Containers.

## Quick Start

### Prerequisites

- Docker Desktop
- Visual Studio Code
- Dev Containers extension for VS Code

### 1. Open in Dev Container

1. Open this project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Dev Containers: Reopen in Container"
4. Wait for the container to build and setup to complete

### 2. Start Development Environment

```bash
# Start the complete development environment
./dev-full.sh
```

This will start:
- 📧 **MailHog** (SMTP server for testing) - `http://localhost:8025`
- 🔴 **Redis** (for caching/sessions) - `localhost:6379`
- 🪝 **Webhook Tester** (test webhook endpoints) - `http://localhost:8080`
- 🎨 **UI Development Server** - `http://localhost:3000`
- ⚡ **Backend API** - `http://localhost:8000`

### 3. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **UI Development** | http://localhost:3000 | Vue.js frontend with hot reload |
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **MailHog** | http://localhost:8025 | Email testing (SMTP: localhost:1025) |
| **Webhook Tester** | http://localhost:8080 | Test webhook endpoints |

## Development Workflow

### Backend Development

```bash
# Start only backend with auto-reload
./dev-backend.sh

# Run tests
./test.sh

# Format code
black imageroot/pypkg/mailwebhook/

# Lint code
flake8 imageroot/pypkg/mailwebhook/
```

### Frontend Development

```bash
# Start only UI development server
./dev-ui.sh

# In ui/ directory:
cd ui
npm run serve    # Development server
npm run build    # Production build
npm run lint     # Lint Vue.js code
```

### Full Stack Testing

1. **Send Test Email**: Use MailHog to send test emails
2. **Configure Webhook**: Use Webhook Tester to create test endpoints
3. **Create Schedule**: Use the UI to create email processing schedules
4. **Monitor Logs**: Check console output for real-time processing

## Project Structure

```
ns8-mail-webhook/
├── .devcontainer/           # Dev container configuration
│   ├── devcontainer.json   # VS Code dev container settings
│   ├── setup.sh            # Container setup script
│   └── requirements-dev.txt # Development dependencies
├── imageroot/              # NethServer 8 module files
│   ├── actions/           # Module actions (create, configure, etc.)
│   ├── bin/               # Executables and scripts
│   ├── pypkg/             # Python package
│   │   └── mailwebhook/   # Main application code
│   └── systemd/           # Systemd service files
├── ui/                    # Vue.js frontend
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── dist/             # Built files (after npm run build)
├── tests/                # Robot Framework tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Production Docker image
└── docker-compose.dev.yml # Development services
```

## Development Scripts

| Script | Purpose |
|--------|---------|
| `./dev-full.sh` | Start complete development environment |
| `./dev-backend.sh` | Start only backend API |
| `./dev-ui.sh` | Start only UI development server |
| `./test.sh` | Run all tests |
| `./build-dev.sh` | Build development Docker image |

## Testing Email Processing

### 1. Configure MailHog

MailHog is already configured and running at `http://localhost:8025`

```python
# In your test code, use these settings:
IMAP_HOST = "localhost"
IMAP_PORT = 1025  # MailHog SMTP port
```

### 2. Send Test Emails

```bash
# Using mail command (if available)
echo "Test email body" | mail -s "Test Subject" test@example.com

# Or use MailHog web interface
# Go to http://localhost:8025 and use the built-in composer
```

### 3. Test Webhooks

1. Go to `http://localhost:8080` (Webhook Tester)
2. Create a new webhook endpoint
3. Use the provided URL in your module configuration
4. Send emails and watch for webhook calls

## API Testing

### Using curl

```bash
# Check status
curl http://localhost:8000/api/status

# Create a schedule
curl -X POST http://localhost:8000/api/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "mailbox_to_monitor": "test@example.com",
    "webhook_url": "http://localhost:8080/webhook/123",
    "payload_format": "JSON",
    "is_active": true
  }'

# List schedules
curl http://localhost:8000/api/schedules/

# Get logs
curl http://localhost:8000/api/logs/
```

### Using the Interactive Docs

Visit `http://localhost:8000/docs` for interactive API documentation where you can test all endpoints directly.

## Building for Production

### Local Build

```bash
# Build the complete module
./build-dev.sh

# Test the built image
docker run -p 8000:8000 ns8-mail-webhooks:dev
```

### NethServer 8 Build

```bash
# Build using buildah (NS8 style)
./build-images.sh

# Or using Docker
./build-docker.sh
```

## Debugging

### Backend Debugging

The dev container includes debugpy for Python debugging:

1. Set breakpoints in VS Code
2. Press F5 to start debugging
3. The backend will start with debugger attached

### Frontend Debugging

1. Open browser developer tools
2. Set breakpoints in the Sources tab
3. Vue.js devtools extension is recommended

### Log Analysis

```bash
# Backend logs
tail -f logs/backend.log

# Container logs
docker logs $(docker ps -q --filter name=mail-webhooks)
```

## Environment Variables

Development environment variables are in `.env.dev`:

```bash
IMAP_HOST=127.0.0.1
IMAP_PORT=993
POLLING_INTERVAL=60
WEBHOOK_TIMEOUT=30
DATABASE_URL=sqlite:///./data/schedules.db
DEBUG=true
LOG_LEVEL=DEBUG
```

## Troubleshooting

### Container Issues

```bash
# Rebuild dev container
Ctrl+Shift+P > "Dev Containers: Rebuild Container"

# View container logs
docker logs vsc-ns8-mail-webhook-...
```

### Service Issues

```bash
# Check running services
docker-compose -f docker-compose.dev.yml ps

# Restart services
docker-compose -f docker-compose.dev.yml restart

# View service logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Port Conflicts

If ports are already in use, modify the ports in:
- `.devcontainer/devcontainer.json` (forwardPorts)
- `docker-compose.dev.yml` (services ports)

## Contributing

1. Make changes in your dev container
2. Test thoroughly using the development environment
3. Run `./test.sh` to ensure all tests pass
4. Format code with `black` and lint with `flake8`
5. Commit and push your changes

## VS Code Extensions

The dev container automatically installs these helpful extensions:

- **Python**: Python language support
- **Pylance**: Python language server
- **Black Formatter**: Python code formatting
- **Vue**: Vue.js language support
- **Docker**: Docker support
- **YAML**: YAML language support
- **GitLens**: Enhanced Git capabilities

Happy coding! 🚀
