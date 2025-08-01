#!/bin/bash

# Pinterest AI Agent - EC2 User Data Script
# This script runs on first boot of the EC2 instance

set -e  # Exit on any error

echo "Starting Pinterest AI Agent deployment..."

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    unzip

# Install Docker
echo "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/app
cd /opt/app

# Clone the repository
echo "Cloning repository..."
git clone https://github.com/shniss/Pinterest-Scraper-Public.git .
mkdir -p backend frontend deployment

# Copy environment files
echo "Setting up environment files..."
cd deployment

# Get EC2 public IP for CORS configuration
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Create environment files if they don't exist
if [ ! -f .env.backend ]; then
    cat > .env.backend << EOF
# Mongo Connection (Required)
MONGO_URI=mongodb://admin:password123@mongodb:27017/pinterest_agent?authSource=admin

# Redis Connection (Required for Celery)
REDIS_URL=redis://redis:6379

# OpenAI API Key (Required for image validation)
OPENAI_API_KEY=your-openai-api-key-here

# Pinterest account password (this will be resolved by the seed script)
PIN_PASSWORD=your-pinterest-password-here

# Proxy password (this will be resolved by the seed script)
PROXY_PASSWORD=your-proxy-password-here

# Server Settings
HOST=0.0.0.0
PORT=8000

# Default User Agent
DEFAULT_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# As a fallback
PIN_EMAIL=your-pinterest-email-here
PIN_USERNAME=your-pinterest-username-here
PROXY_SERVER=your-proxy-server-here
PROXY_USERNAME=your-proxy-username-here
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:3000,http://localhost:*,http://${EC2_PUBLIC_IP},http://${EC2_PUBLIC_IP}:80,http://${EC2_PUBLIC_IP}:8000
EOF
fi

if [ ! -f .env.frontend ]; then
    cat > .env.frontend << EOF
# Frontend Environment Variables
NEXT_PUBLIC_API_URL=http://${EC2_PUBLIC_IP}:8000
NODE_ENV=production
EOF
fi

echo "⚠️  IMPORTANT: Please complete the setup:"
echo "   2. Edit .env.backend with your actual API keys and passwords"
echo "   3. Edit .env.frontend if needed"
echo "   4. Then run: docker compose up -d"

# Set proper permissions
chmod +x seed_pinterest_accounts.py

# Go back to root directory for docker-compose
cd /opt/app

# Pull Docker images and build
echo "📦 Building Docker images..."
docker compose build

# Start the seed service first
echo "🌱 Running seed service..."
docker compose up -d --build seed

# Wait for seed to complete
echo "⏳ Waiting for seed service to complete..."
sleep 30

# Start the full stack
echo "🚀 Starting full application stack..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 60

# Check service status
echo "📊 Checking service status..."
docker compose ps

echo "✅ Deployment completed!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "   Backend API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   API Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
echo ""
echo "📝 Next steps:"
echo "   1. SSH into the instance: ssh ubuntu@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "   2. Edit environment files: cd /opt/app/deployment && nano .env.backend"
echo "   3. Restart services: docker compose restart"
echo ""
echo "🔍 Useful commands:"
echo "   - View logs: docker compose logs -f"
echo "   - Check status: docker compose ps"
echo "   - Restart services: docker compose restart"
echo "   - Stop services: docker compose down" 