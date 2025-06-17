# NS8 Mail Webhooks Module - Implementation Guide

## Project Overview

**Module Name**: ns8-mail-webhooks  
**Repository**: https://github.com/leemlwando/ns8-mail-webhooks  
**Container Registry**: ghcr.io/leemlwando/ns8-mail-webhooks  
**Purpose**: Create webhook triggers for incoming mail with configurable intervals, payload types, and management interface  
**Date Started**: June 17, 2025  
**NS8 Framework**: Based on ns8-kickstart template

## Requirements Analysis

### Core Features
1. **Webhook Triggers**
   - Create triggers for incoming mail
   - Support specified intervals (real-time + scheduled)
   - Configurable webhook URLs with optional API keys
   
2. **Payload Types**
   - RAW format (email content as-is)
   - JSON format (structured email metadata + content)
   
3. **UI Management**
   - List all configured webhooks
   - CRUD operations (Create, Read, Update, Delete)
   - Edit webhook configurations
   
4. **Settings Page**
   - Database URL configuration (MongoDB)
   - Mail server integration settings
   
5. **Authentication**
   - Similar mechanism to ns8-roundcubemail
   - Access mailboxes through existing mail module authentication
   - Real-time incoming mail triggers

## Architecture Design

### Backend Components

#### 1. Database Layer (MongoDB)
```
Collections:
- webhooks: Store webhook configurations
- triggers: Store trigger schedules and metadata  
- mail_events: Track processed mail events
- settings: Module configuration
```

#### 2. Mail Integration
```
Integration Points:
- Dovecot mail server (from ns8-mail)
- LDAP authentication (reuse from mail module)
- IMAP access for mailbox monitoring
- Push notifications or IMAP IDLE for real-time triggers
```

#### 3. Webhook Engine
```
Components:
- Scheduler service (cron-like intervals)
- Real-time processor (on mail arrival)
- HTTP client with retry logic
- Payload formatters (RAW/JSON)
```

#### 4. API Layer
```
Endpoints:
- /api/webhooks (CRUD operations)
- /api/settings (configuration)
- /api/status (monitoring)
- /api/test (webhook testing)
```

### Frontend Components

#### 1. Webhooks Management Page
- Webhook list table with actions
- Add/Edit webhook modal
- Delete confirmation
- Test webhook functionality

#### 2. Settings Page  
- MongoDB connection settings
- Mail server selection
- Authentication configuration

## Technical Stack

### Backend
- **Language**: Python 3.11
- **Database**: MongoDB with pymongo driver (configurable URL)
- **Web Framework**: FastAPI (async, auto-documentation, Pydantic validation)
- **HTTP Client**: requests library
- **Scheduling**: APScheduler for interval-based triggers (Phase 2)

### Frontend
- **Framework**: Vue.js 2 (consistent with other NS8 modules)
- **UI Library**: Carbon Design System
- **State Management**: Vuex
- **HTTP Client**: axios

### Integration
- **Authentication**: LDAP via ns8-mail module
- **Service Discovery**: Redis-based (NS8 pattern)
- **Routing**: Traefik integration
- **Containerization**: Podman containers

## Implementation Phases

### Phase 1: Backend Foundation ✅ COMPLETED
1. **External MongoDB Integration** ✅ COMPLETED
   - ✅ External MongoDB connection via configurable URL
   - ✅ No self-hosted MongoDB instance required
   - ✅ Connection validation and graceful error handling
   
2. **Basic API Layer** ✅ COMPLETED
   - ✅ FastAPI application with Pydantic models
   - ✅ Complete webhook CRUD endpoints
   - ✅ Settings management endpoints
   - ✅ Configuration actions (configure-module, get-configuration)
   - ✅ Health check and test endpoints

**Approach**: Simplified, production-ready implementation with focus on code readability
**Key Decisions**: 
- ✅ FastAPI for modern async API with automatic documentation
- ✅ External MongoDB only - no self-hosted database management
- ✅ Pydantic models for data validation
- ✅ Graceful startup without requiring immediate MongoDB connection

### Phase 2: Mail Integration ⏳ NEXT
3. **Mail Server Discovery** 
   - ✅ Service discovery integration (get-configuration action)
   - ⏳ LDAP authentication integration
   - ⏳ Mailbox access configuration
   
4. **Mail Monitoring**
   - ⏳ IMAP connection management
   - ⏳ Real-time mail event detection
   - ⏳ Mail parsing and metadata extraction

### Phase 3: Webhook Engine
5. **Webhook Processing**
   - HTTP webhook delivery
   - Retry logic and error handling
   - Payload formatting (RAW/JSON)
   
6. **Scheduling System**
   - Interval-based triggers
   - Cron-like scheduling
   - Event queue management

### Phase 4: Frontend Development
7. **UI Foundation**
   - Vue.js setup with Carbon components
   - Router and state management
   - Basic layout and navigation
   
8. **Webhooks Management**
   - Webhook list view
   - Add/Edit forms
   - Delete functionality
   
9. **Settings Page**
   - Database configuration
   - Mail server settings
   - Testing utilities

### Phase 5: Integration & Polish
10. **Full Integration**
    - End-to-end testing
    - Performance optimization
    - Error handling improvements
    
11. **Documentation & Deployment**
    - User documentation
    - API documentation
    - Deployment scripts

## File Structure

```
mail-webhooks-v0.1.0/
├── IMPLEMENTATION.md              # This file
├── README.md                      # Module documentation
├── build-images.sh               # Container build script
├── test-module.sh                # Testing script
├── imageroot/
│   ├── actions/
│   │   ├── configure-module/      # Module configuration
│   │   ├── create-webhook/        # Webhook CRUD
│   │   ├── delete-webhook/
│   │   ├── get-webhooks/
│   │   ├── update-webhook/
│   │   ├── test-webhook/
│   │   └── get-configuration/
│   ├── bin/
│   │   ├── mail-monitor          # Mail monitoring service
│   │   └── webhook-processor     # Webhook execution engine
│   ├── events/
│   │   └── mail-settings-changed/
│   ├── systemd/user/
│   │   └── mail-webhooks.service    # Main API service (no MongoDB service)
│   └── templates/
├── ui/
│   ├── src/
│   │   ├── components/
│   │   │   ├── WebhooksList.vue
│   │   │   ├── WebhookForm.vue
│   │   │   └── TestWebhook.vue
│   │   ├── views/
│   │   │   ├── Status.vue
│   │   │   ├── Settings.vue
│   │   │   └── Webhooks.vue
│   │   └── router/
│   └── public/
└── tests/
```

## Database Schema

### Webhooks Collection
```javascript
{
  _id: ObjectId,
  name: String,          // User-friendly name
  url: String,           // Webhook URL
  api_key: String,       // Optional API key
  payload_type: String,  // "RAW" or "JSON"
  trigger_type: String,  // "realtime" or "interval"
  interval: Number,      // Minutes for interval triggers
  mailboxes: [String],   // Monitored mailboxes
  filters: {             // Mail filters
    subject: String,
    sender: String,
    folder: String
  },
  active: Boolean,
  created_at: Date,
  updated_at: Date,
  last_triggered: Date
}
```

### Mail Events Collection
```javascript
{
  _id: ObjectId,
  webhook_id: ObjectId,
  message_id: String,
  mailbox: String,
  subject: String,
  sender: String,
  timestamp: Date,
  processed: Boolean,
  webhook_response: {
    status_code: Number,
    response_time: Number,
    error: String
  }
}
```

### Settings Collection
```javascript
{
  _id: ObjectId,
  mongodb_url: String,
  mail_server_uuid: String,
  mail_domain: String,
  max_retries: Number,
  retry_delay: Number,
  updated_at: Date
}
```

## Integration Points

### NS8-Mail Integration
- **Service Discovery**: Use Redis to find mail server instance
- **Authentication**: Leverage existing LDAP configuration
- **Mailbox Access**: Use Dovecot API or direct IMAP access
- **User Domain**: Inherit from mail server configuration

### Traefik Integration
- **Web UI**: Route `/mail-webhooks` to frontend
- **API**: Route `/mail-webhooks/api` to backend
- **Security**: Use same authentication as other NS8 modules

### MongoDB Integration
- **Container**: Use official MongoDB image
- **Persistence**: Store data in named volumes
- **Configuration**: Environment-based connection strings

## API Endpoints Design

### Webhooks Management
```
GET    /api/webhooks           # List all webhooks
POST   /api/webhooks           # Create webhook
GET    /api/webhooks/{id}      # Get webhook details
PUT    /api/webhooks/{id}      # Update webhook
DELETE /api/webhooks/{id}      # Delete webhook
POST   /api/webhooks/{id}/test # Test webhook
```

### Configuration
```
GET    /api/settings           # Get configuration
PUT    /api/settings           # Update configuration
GET    /api/mail-servers       # List available mail servers
```

### Monitoring
```
GET    /api/status             # Service status
GET    /api/events             # Recent mail events
GET    /api/webhooks/{id}/logs # Webhook execution logs
```

## Security Considerations

1. **Input Validation**: Validate all webhook URLs and configurations
2. **API Key Storage**: Encrypt API keys in database
3. **Authentication**: Use NS8 authentication mechanisms
4. **Network Security**: Validate webhook URLs, prevent SSRF
5. **Rate Limiting**: Prevent webhook abuse

## Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test mail server integration
3. **E2E Tests**: Test complete webhook workflows
4. **Performance Tests**: Test under load
5. **Security Tests**: Validate security measures

## Deployment Considerations

1. **Container Images**: Build and push to registry
2. **Dependencies**: MongoDB, mail server integration
3. **Resource Requirements**: CPU, memory, storage
4. **Backup Strategy**: MongoDB data backup
5. **Monitoring**: Health checks and alerting

## Questions & Decisions Log

### Resolved
- **Database Choice**: MongoDB selected for flexibility with email data
- **Web Framework**: Flask chosen for simplicity and NS8 consistency
- **UI Framework**: Vue.js 2 with Carbon Design for NS8 consistency

### Pending
- **Trigger Intervals**: What specific intervals are needed?
- **Mail Scope**: All mailboxes or configurable selection?
- **Payload Details**: Exact structure for RAW vs JSON formats?
- **Authentication Methods**: What webhook auth methods to support?
- **Mail Filtering**: What filtering capabilities are required?

## Next Steps

1. **Immediate**: ✅ COMPLETED - Phase 1 Backend Foundation with Collection Configuration
2. **Current**: 🔄 Start Phase 2 - Mail Integration
   - Implement mail server discovery and authentication
   - Create IMAP monitoring service
   - Test webhook delivery system with custom collections
3. **Next**: Plan frontend mockups and basic Vue.js setup

---

**Last Updated**: June 17, 2025  
**Current Phase**: Phase 1 ✅ COMPLETED (including collection configuration), Starting Phase 2  
**Next Milestone**: Mail server integration and IMAP monitoring

## Phase 1 Completed ✅

### What's Working:
- ✅ FastAPI application with complete CRUD operations for webhooks
- ✅ External MongoDB integration with configurable connection URL
- ✅ **Custom Collection Names Support** - Users can override default collection names
- ✅ Pydantic models for data validation
- ✅ Systemd service for API (no MongoDB management required)
- ✅ Configuration management with required MongoDB URL validation
- ✅ Health checks and webhook testing endpoints
- ✅ Traefik integration for web routing
- ✅ **Dynamic collection access** - All API endpoints use configurable collection names
- ✅ **Settings UI** - Web interface to configure MongoDB URL and collection names
- ✅ Graceful startup and error handling

### Collection Configuration Features:
- ✅ **Environment Variables**: Collection names can be set via environment during configure-module
- ✅ **Runtime Settings**: Collection names can be changed via the Settings UI
- ✅ **JSON Schema Validation**: Collection names must follow MongoDB naming rules
- ✅ **Dynamic Collection Access**: All API operations use current collection configuration
- ✅ **Index Management**: Indexes are created on custom collections automatically

**Available Collection Overrides:**
- `webhooks_collection` (default: "webhooks") - Webhook configurations
- `events_collection` (default: "events") - Mail events and execution logs  
- `settings_collection` (default: "settings") - Module settings
- `triggers_collection` (default: "triggers") - Trigger scheduling information
- `logs_collection` (default: "logs") - Execution logs and debugging

### API Endpoints Ready:
- `GET /health` - Service health check
- `GET /api/webhooks` - List all webhooks
- `POST /api/webhooks` - Create new webhook
- `GET /api/webhooks/{id}` - Get webhook details
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings
- `GET /api/events` - List mail events

### Ready for Testing:
The backend API is ready for testing with tools like curl or Postman. MongoDB connection and collection names are configurable via the settings API or configure-module action.
