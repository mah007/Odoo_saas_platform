#!/bin/bash

# Odoo SaaS Platform - One-Click Deployment Script
# This script deploys the complete platform with zero technical interaction

set -e

echo "🚀 Starting Odoo SaaS Platform Deployment..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. This is not recommended for production."
fi

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "📋 Step 1: System Requirements Check"
print_status "Checking system requirements..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo apt update
    sudo apt install -y docker-compose-plugin
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Install other required packages
print_status "Installing system dependencies..."
sudo apt update
sudo apt install -y curl wget git htop net-tools ufw

print_header "🔧 Step 2: Environment Configuration"

# Generate secure passwords and keys
print_status "Generating secure configuration..."

POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "localhost")

# Create .env file
cat > .env << EOF
# Odoo SaaS Platform Configuration
# Generated automatically on $(date)

# Database Configuration
POSTGRES_DB=odoo_saas_platform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/odoo_saas_platform

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Security Configuration
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Domain Configuration
DOMAIN=host.odoo-egypt.com
SERVER_IP=${SERVER_IP}

# CORS Configuration
ALLOWED_ORIGINS=https://host.odoo-egypt.com,http://host.odoo-egypt.com,http://localhost:3000,http://${SERVER_IP}
ALLOWED_HOSTS=host.odoo-egypt.com,localhost,${SERVER_IP}

# Admin Configuration
ADMIN_EMAIL=admin@odoo-egypt.com
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# Email Configuration (Configure later)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@odoo-egypt.com
SMTP_FROM_NAME=Odoo SaaS Platform

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_PATH=/app/uploads

# Odoo Configuration
ODOO_DOCKER_IMAGE=odoo:17.0
ODOO_BASE_PORT=8069
ODOO_INSTANCES_PATH=/app/odoo-instances

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Backup Configuration
BACKUP_STORAGE_TYPE=local
BACKUP_RETENTION_DAYS=30

# Monitoring
PROMETHEUS_ENABLED=true

# Celery Configuration
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

# Grafana Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=${ADMIN_PASSWORD}
EOF

print_status "Environment configuration created"

print_header "🔥 Step 3: Firewall Configuration"
print_status "Configuring firewall..."

# Configure UFW firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

print_status "Firewall configured successfully"

print_header "🐳 Step 4: Building and Starting Services"
print_status "Building Docker images..."

# Build and start all services
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

print_status "Waiting for services to start..."
sleep 30

# Check service health
print_status "Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:80/health > /dev/null; then
        print_status "Services are healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Services failed to start properly"
        docker-compose logs --tail=20
        exit 1
    fi
    sleep 2
done

print_header "🎯 Step 5: Database Initialization"
print_status "Initializing database and creating admin user..."

# Wait for database to be ready
sleep 10

# Initialize database and create admin user
docker-compose exec -T backend python -c "
import asyncio
import sys
sys.path.append('/app')

async def init_system():
    from app.core.database import init_db
    from app.services.admin import create_admin_user
    
    try:
        await init_db()
        await create_admin_user()
        print('Database initialized and admin user created successfully')
    except Exception as e:
        print(f'Initialization error: {e}')
        
asyncio.run(init_system())
" || print_warning "Database initialization may need manual setup"

print_header "✅ Deployment Complete!"
echo "=================================================="
print_status "Odoo SaaS Platform is now running!"
echo ""
print_header "🌐 Access Information:"
echo "Main Website:      http://${SERVER_IP}"
echo "Admin Dashboard:   http://${SERVER_IP}/admin"
echo "API Documentation: http://${SERVER_IP}/docs"
echo "Monitoring:        http://${SERVER_IP}:3001 (Grafana)"
echo ""
print_header "🔐 Admin Credentials:"
echo "Email:    admin@odoo-egypt.com"
echo "Password: ${ADMIN_PASSWORD}"
echo ""
print_header "🔧 Service Status:"
docker-compose ps

echo ""
print_header "📝 Next Steps:"
echo "1. Access the admin dashboard to configure tenants"
echo "2. Set up email configuration in .env file"
echo "3. Configure SSL certificates for production"
echo "4. Set up domain DNS to point to ${SERVER_IP}"
echo ""
print_status "For support, check the logs: docker-compose logs -f"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"

echo ""
print_header "🎉 Odoo SaaS Platform is ready to use!"

