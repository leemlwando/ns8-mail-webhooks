# NS8 Mail Webhooks Module

A NetherServer 8 module for creating and managing mail webhooks that trigger HTTP callbacks when mail events occur.

## Features

- **Webhook Management**: Create, edit, delete and test webhooks through a modern web interface
- **Multiple Trigger Types**: Support for realtime and interval-based triggers
- **Flexible Payload Formats**: JSON and RAW payload support
- **MongoDB Integration**: Scalable storage with configurable collection names
- **Mail Server Integration**: Optional integration with NS8 mail servers
- **Secure API**: RESTful API with authentication support
- **Modern UI**: Built with Vue.js and Carbon Design System
- **Container-based**: Runs in isolated containers for security and scalability

## Architecture

### Components

1. **Web UI** (`ui/`): Vue.js application with NS8-compliant interface
2. **Backend API** (`imageroot/api/`): FastAPI-based REST API server
3. **Actions** (`imageroot/actions/`): NS8 agent task handlers
4. **Mail Integrations** (`imageroot/api/`): IMAP monitoring and mail discovery

### Technology Stack

- **Frontend**: Vue 2.x, Carbon Design System, ns8-ui-lib
- **Backend**: Python 3.x, FastAPI, PyMongo, Uvicorn
- **Database**: MongoDB (configurable connection)
- **Container**: Podman/Docker compatible
- **Web Server**: Traefik integration for routing and SSL

## Installation

### Prerequisites

- NetherServer 8 cluster
- MongoDB instance (local or remote)
- Available TCP port for the service

### Install from NS8 Software Center

1. Open the NS8 Software Center
2. Search for "Mail Webhooks"
3. Click Install and follow the configuration wizard

### Manual Installation

```bash
# Add the module to your NS8 cluster
add-module ghcr.io/nethserver/mail-webhooks:latest 1
```

## Configuration

### Basic Configuration

The module requires minimal configuration to get started:

1. **Hostname**: FQDN for accessing the webhook interface
2. **MongoDB URL**: Connection string to your MongoDB instance

### Advanced Configuration

- **Mail Server UUID**: Link to specific NS8 mail server instance
- **Collection Names**: Customize MongoDB collection names
- **SSL Certificate**: Enable Let's Encrypt automatic certificate

### MongoDB Connection Examples

```bash
# Local MongoDB
mongodb://localhost:27017/mailwebhooks

# MongoDB with authentication
mongodb://user:password@host:27017/database

# MongoDB Atlas (cloud)
mongodb+srv://user:password@cluster.mongodb.net/database

# MongoDB replica set
mongodb://user:password@host1:27017,host2:27017/database?replicaSet=rs0
```

## Usage

### Web Interface

Access the web interface at your configured hostname:

```
https://your-hostname/
```

The interface provides:

- **Status**: View service status and system information
- **Webhooks**: Manage webhook configurations
- **Settings**: Configure module settings
- **About**: View version and license information

### Creating Webhooks

1. Navigate to the **Webhooks** section
2. Click **Create Webhook**
3. Configure:
   - **Name**: Descriptive name for the webhook
   - **URL**: Target HTTP endpoint
   - **API Key**: Optional authentication token
   - **Payload Type**: JSON or RAW format
   - **Trigger Type**: Realtime or interval-based
   - **Filters**: Email filtering criteria

### API Usage

The module exposes a REST API for programmatic access:

```bash
# List webhooks
curl -X GET http://localhost:8080/api/webhooks

# Create webhook
curl -X POST http://localhost:8080/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Webhook",
    "url": "https://example.com/webhook",
    "payload_type": "JSON",
    "trigger_type": "realtime",
    "active": true
  }'

# Test webhook
curl -X POST http://localhost:8080/api/webhooks/{id}/test
```

## Actions Reference

The module provides several NS8 actions for management:

### Core Actions

- `configure-module`: Configure module settings
- `get-configuration`: Retrieve current configuration
- `get-status`: Get service status and metrics
- `get-name`: Get module instance name

### Webhook Actions

- `list-webhooks`: List all configured webhooks
- `create-webhook`: Create a new webhook
- `update-webhook`: Update existing webhook
- `delete-webhook`: Remove webhook

### Utility Actions

- `test-module`: Run module health checks
- `test-deployment`: Validate deployment configuration

## Development

### Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Podman or Docker
- NS8 development environment

### Build Instructions

```bash
# Clone the repository
git clone https://github.com/nethserver/ns8-mail-webhooks.git
cd ns8-mail-webhooks

# Build UI
cd ui
npm install
npm run build
cd ..

# Build container images
./build-images.sh
```

### Local Development

```bash
# Start development UI server
cd ui
npm run serve

# Start API server
cd imageroot/api
pip install -r requirements.txt
python app.py
```

### Testing

```bash
# Run UI tests
cd ui
npm run test

# Run Python tests
cd imageroot
python -m pytest tests/

# Test module actions
runagent python3 actions/test-module/10test
```

## Troubleshooting

### Common Issues

#### MongoDB Connection Failed
- Verify MongoDB URL format and credentials
- Check network connectivity to MongoDB server
- Ensure MongoDB service is running

#### Service Not Starting
- Check systemd service status: `systemctl --user status mail-webhooks.service`
- Verify container image is available: `podman images`
- Check environment variables: `cat ~/.config/state/environment`

#### UI Not Accessible
- Verify Traefik configuration: `curl -H "Host: your-hostname" http://127.0.0.1:port`
- Check DNS resolution for configured hostname
- Verify SSL certificate if HTTPS is enabled

### Log Files

- **Service logs**: `journalctl --user -u mail-webhooks.service -f`
- **Container logs**: `podman logs mail-webhooks`
- **Agent logs**: `tail -f /var/log/ns8-agent.log`

### Debug Mode

Enable debug logging by setting environment variables:

```bash
# Enable debug logging
echo "DEBUG=true" >> ~/.config/state/environment
systemctl --user restart mail-webhooks.service
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Guidelines

- Follow NS8 module standards and conventions
- Use proper error handling and logging
- Write tests for new functionality
- Update documentation for changes
- Follow code style guidelines

## License

This project is licensed under the GPL-3.0-or-later License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [NS8 Mail Webhooks Docs](https://docs.nethserver.org/mail-webhooks/)
- **Community Forum**: [NethServer Community](https://community.nethserver.org/)
- **Issue Tracker**: [GitHub Issues](https://github.com/nethserver/ns8-mail-webhooks/issues)
- **Professional Support**: [Nethesis S.r.l.](https://www.nethesis.it/)

## Acknowledgments

- Built on the [NS8 Kickstart](https://github.com/nethserver/ns8-kickstart) foundation
- Uses the [NS8 UI Library](https://github.com/nethserver/ns8-ui-lib) for interface components
- Inspired by the [NS8 WebTop](https://github.com/nethserver/ns8-webtop) module architecture
