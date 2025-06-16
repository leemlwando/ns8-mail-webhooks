#!/bin/bash

#
# Development container setup script for NS8 Mail Webhooks
#

set -e

echo "🚀 Setting up NS8 Mail Webhooks development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install --user -r requirements.txt
fi

# Install additional development tools
echo "🔧 Installing development tools..."
pip install --user black flake8 pytest pytest-asyncio httpx

# Install Node.js dependencies for UI
echo "🎨 Installing UI dependencies..."
if [ -d ui ]; then
    cd ui
    npm install
    cd ..
fi

# Create development directories
echo "📁 Creating development directories..."
mkdir -p logs
mkdir -p data

# Set up git hooks (optional)
echo "🎣 Setting up git hooks..."
if [ -d .git ]; then
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Format Python code with black
black --check imageroot/pypkg/mailwebhook/ || (echo "Run 'black imageroot/pypkg/mailwebhook/' to fix formatting" && exit 1)
# Lint with flake8
flake8 imageroot/pypkg/mailwebhook/ || exit 1
EOF
    chmod +x .git/hooks/pre-commit
fi

# Create environment file for development
echo "⚙️ Creating development environment..."
cat > .env.dev << 'EOF'
# Development Environment Variables
IMAP_HOST=127.0.0.1
IMAP_PORT=993
POLLING_INTERVAL=60
WEBHOOK_TIMEOUT=30
DATABASE_URL=sqlite:///./data/schedules.db
DEBUG=true
LOG_LEVEL=DEBUG
EOF

# Create docker-compose for development services
echo "🐳 Creating docker-compose for development..."
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    environment:
      - MH_STORAGE=maildir
      - MH_MAILDIR_PATH=/maildir
    volumes:
      - mailhog_data:/maildir

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  webhook-tester:
    image: tarampampam/webhook-tester:latest
    ports:
      - "8080:8080"

volumes:
  mailhog_data:
  redis_data:
EOF

# Create development scripts
echo "🛠️ Creating development scripts..."

# Backend development script
cat > dev-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting backend in development mode..."
export PYTHONPATH="${PWD}/imageroot/pypkg:${PYTHONPATH}"
cd imageroot/pypkg
uvicorn mailwebhook.main:app --reload --host 0.0.0.0 --port 8000 --env-file ../../.env.dev
EOF
chmod +x dev-backend.sh

# UI development script  
cat > dev-ui.sh << 'EOF'
#!/bin/bash
echo "🎨 Starting UI in development mode..."
cd ui
npm run serve
EOF
chmod +x dev-ui.sh

# Full development environment script
cat > dev-full.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting full development environment..."
echo "📧 Starting mail services..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to start..."
sleep 5

echo "🎨 Starting UI and Backend..."
echo "UI will be available at: http://localhost:3000"
echo "Backend API will be available at: http://localhost:8000"
echo "MailHog UI will be available at: http://localhost:8025"
echo "Webhook Tester will be available at: http://localhost:8080"

# Start both UI and backend in background
./dev-ui.sh &
./dev-backend.sh &

wait
EOF
chmod +x dev-full.sh

# Testing script
cat > test.sh << 'EOF'
#!/bin/bash
echo "🧪 Running tests..."

# Backend tests
echo "Testing backend..."
export PYTHONPATH="${PWD}/imageroot/pypkg:${PYTHONPATH}"
cd imageroot/pypkg
python -m pytest tests/ -v

# UI tests
echo "Testing UI..."
cd ../../ui
npm run test:unit || echo "No UI tests configured yet"

echo "✅ Tests completed"
EOF
chmod +x test.sh

# Build script for development
cat > build-dev.sh << 'EOF'
#!/bin/bash
echo "🏗️ Building for development..."

# Build UI
cd ui
npm run build
cd ..

# Build backend image
docker build -t ns8-mail-webhooks:dev .

echo "✅ Development build completed"
echo "🚀 Run: docker run -p 8000:8000 ns8-mail-webhooks:dev"
EOF
chmod +x build-dev.sh

echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Quick Start Commands:"
echo "  ./dev-full.sh    - Start complete development environment"
echo "  ./dev-backend.sh - Start only backend API"
echo "  ./dev-ui.sh      - Start only UI development server"
echo "  ./test.sh        - Run all tests"
echo "  ./build-dev.sh   - Build development image"
echo ""
echo "🌐 Service URLs:"
echo "  UI Development:     http://localhost:3000"
echo "  Backend API:        http://localhost:8000"
echo "  API Documentation:  http://localhost:8000/docs"
echo "  MailHog (SMTP):     http://localhost:8025"
echo "  Webhook Tester:     http://localhost:8080"
echo ""
echo "📚 Development Files:"
echo "  .env.dev                - Environment variables"
echo "  docker-compose.dev.yml  - Development services"
echo "  logs/                   - Application logs"
echo "  data/                   - Development data"
