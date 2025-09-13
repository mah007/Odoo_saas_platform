#!/bin/bash

# Fix and Restart Deployment Script
# This script stops the current deployment, applies fixes, and restarts

echo "🔧 Fixing and restarting Odoo SaaS Platform deployment..."

# Stop all containers
echo "Stopping all containers..."
docker-compose down

# Remove any problematic containers
echo "Cleaning up containers..."
docker container prune -f

# Remove any problematic networks
echo "Cleaning up networks..."
docker network prune -f

# Pull latest images if needed
echo "Pulling latest images..."
docker-compose pull

# Start services with better dependency handling
echo "Starting services step by step..."

# Start core services first
echo "Starting database and cache..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 30

# Start backend
echo "Starting backend..."
docker-compose up -d backend

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 20

# Start frontend services
echo "Starting frontend services..."
docker-compose up -d frontend admin-dashboard

# Wait for frontend services
echo "Waiting for frontend services..."
sleep 20

# Finally start nginx
echo "Starting nginx..."
docker-compose up -d nginx

# Check status
echo "Checking service status..."
docker-compose ps

echo "✅ Deployment restart complete!"
echo ""
echo "🌐 Your services should now be available:"
echo "- Main site: http://host.odoo-egypt.com"
echo "- API: http://api.host.odoo-egypt.com"
echo "- Admin: http://admin.host.odoo-egypt.com"
echo ""
echo "📊 Check logs if needed:"
echo "docker-compose logs -f nginx"
echo "docker-compose logs -f backend"

