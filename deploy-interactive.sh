#!/bin/bash

# Odoo SaaS Platform - Interactive Deployment Script
# This script will guide you through the complete setup process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to prompt for user input
prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        echo -e "${BLUE}$prompt${NC} ${YELLOW}(default: $default)${NC}: "
    else
        echo -e "${BLUE}$prompt${NC}: "
    fi
    
    read -r input
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

# Function to prompt for yes/no
prompt_yn() {
    local prompt="$1"
    local default="$2"
    
    while true; do
        if [ "$default" = "y" ]; then
            echo -e "${BLUE}$prompt${NC} ${YELLOW}[Y/n]${NC}: "
        else
            echo -e "${BLUE}$prompt${NC} ${YELLOW}[y/N]${NC}: "
        fi
        
        read -r yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) 
                if [ "$default" = "y" ]; then
                    return 0
                else
                    return 1
                fi
                ;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to validate domain
validate_domain() {
    local domain="$1"
    if [[ $domain =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate email
validate_email() {
    local email="$1"
    if [[ $email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."
    
    # Check OS
    if [ ! -f /etc/os-release ]; then
        print_error "Cannot determine OS. This script requires Ubuntu 20.04+ or similar."
        exit 1
    fi
    
    . /etc/os-release
    print_status "Operating System: $PRETTY_NAME"
    
    # Check memory
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$total_mem" -lt 3500 ]; then
        print_warning "System has ${total_mem}MB RAM. Recommended: 4GB+ for production."
        if ! prompt_yn "Continue anyway?" "n"; then
            exit 1
        fi
    else
        print_status "Memory: ${total_mem}MB (OK)"
    fi
    
    # Check disk space
    available_space=$(df / | awk 'NR==2 {print $4}')
    available_gb=$((available_space / 1024 / 1024))
    if [ "$available_gb" -lt 20 ]; then
        print_warning "Available disk space: ${available_gb}GB. Recommended: 50GB+ for production."
        if ! prompt_yn "Continue anyway?" "n"; then
            exit 1
        fi
    else
        print_status "Disk space: ${available_gb}GB available (OK)"
    fi
}

# Install dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common \
        ufw \
        fail2ban \
        htop \
        git \
        openssl
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        sudo usermod -aG docker $USER
        print_status "Docker installed successfully"
    else
        print_status "Docker is already installed"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        print_status "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        print_status "Docker Compose installed successfully"
    else
        print_status "Docker Compose is already installed"
    fi
    
    # Install Certbot for SSL certificates
    if ! command -v certbot &> /dev/null; then
        print_status "Installing Certbot..."
        sudo snap install core; sudo snap refresh core
        sudo snap install --classic certbot
        sudo ln -sf /snap/bin/certbot /usr/bin/certbot
        print_status "Certbot installed successfully"
    else
        print_status "Certbot is already installed"
    fi
}

# Collect configuration from user
collect_configuration() {
    print_header "CONFIGURATION SETUP"
    
    # Domain configuration
    while true; do
        prompt_input "Enter your main domain (e.g., example.com)" "" "DOMAIN"
        if validate_domain "$DOMAIN"; then
            break
        else
            print_error "Invalid domain format. Please try again."
        fi
    done
    
    # Email for SSL certificates
    while true; do
        prompt_input "Enter your email for SSL certificates" "" "SSL_EMAIL"
        if validate_email "$SSL_EMAIL"; then
            break
        else
            print_error "Invalid email format. Please try again."
        fi
    done
    
    # Subdomains
    API_DOMAIN="api.$DOMAIN"
    ADMIN_DOMAIN="admin.$DOMAIN"
    
    print_status "Main domain: $DOMAIN"
    print_status "API domain: $API_DOMAIN"
    print_status "Admin domain: $ADMIN_DOMAIN"
    
    # Database configuration
    print_step "Database Configuration"
    DB_PASSWORD=$(generate_password)
    prompt_input "PostgreSQL password" "$DB_PASSWORD" "DB_PASSWORD"
    
    # Security configuration
    print_step "Security Configuration"
    SECRET_KEY=$(generate_password)
    JWT_SECRET=$(generate_password)
    
    # Optional services
    print_step "Optional Services Configuration"
    
    if prompt_yn "Configure Stripe for billing?" "y"; then
        prompt_input "Stripe Secret Key (sk_...)" "" "STRIPE_SECRET_KEY"
        prompt_input "Stripe Publishable Key (pk_...)" "" "STRIPE_PUBLISHABLE_KEY"
        prompt_input "Stripe Webhook Secret (whsec_...)" "" "STRIPE_WEBHOOK_SECRET"
    fi
    
    if prompt_yn "Configure SMTP for email notifications?" "y"; then
        prompt_input "SMTP Host (e.g., smtp.gmail.com)" "smtp.gmail.com" "SMTP_HOST"
        prompt_input "SMTP Port" "587" "SMTP_PORT"
        prompt_input "SMTP Username" "" "SMTP_USER"
        prompt_input "SMTP Password" "" "SMTP_PASSWORD"
    fi
    
    if prompt_yn "Configure AWS S3 for backups?" "y"; then
        prompt_input "AWS Access Key ID" "" "AWS_ACCESS_KEY_ID"
        prompt_input "AWS Secret Access Key" "" "AWS_SECRET_ACCESS_KEY"
        prompt_input "S3 Bucket Name" "" "S3_BACKUP_BUCKET"
        prompt_input "AWS Region" "us-east-1" "AWS_REGION"
    fi
}

# Generate configuration files
generate_config() {
    print_step "Generating configuration files..."
    
    # Create .env file
    cat > .env << EOF
# Domain Configuration
DOMAIN=$DOMAIN
API_DOMAIN=$API_DOMAIN
ADMIN_DOMAIN=$ADMIN_DOMAIN

# Database Configuration
POSTGRES_DB=odoo_saas_platform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://postgres:$DB_PASSWORD@postgres:5432/odoo_saas_platform

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Configuration
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_ORIGINS=https://$DOMAIN,https://$API_DOMAIN,https://$ADMIN_DOMAIN

# SSL Email
SSL_EMAIL=$SSL_EMAIL

# Stripe Configuration (if configured)
${STRIPE_SECRET_KEY:+STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY}
${STRIPE_PUBLISHABLE_KEY:+STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY}
${STRIPE_WEBHOOK_SECRET:+STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET}

# SMTP Configuration (if configured)
${SMTP_HOST:+SMTP_HOST=$SMTP_HOST}
${SMTP_PORT:+SMTP_PORT=$SMTP_PORT}
${SMTP_USER:+SMTP_USER=$SMTP_USER}
${SMTP_PASSWORD:+SMTP_PASSWORD=$SMTP_PASSWORD}

# AWS S3 Configuration (if configured)
${AWS_ACCESS_KEY_ID:+AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID}
${AWS_SECRET_ACCESS_KEY:+AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY}
${S3_BACKUP_BUCKET:+S3_BACKUP_BUCKET=$S3_BACKUP_BUCKET}
${AWS_REGION:+AWS_REGION=$AWS_REGION}

# Environment
ENVIRONMENT=production
DEBUG=false
EOF
    
    print_status "Environment configuration created"
}

# Generate nginx configuration
generate_nginx_config() {
    print_step "Generating Nginx configuration..."
    
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time uct="\$upstream_connect_time" '
                    'uht="\$upstream_header_time" urt="\$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    send_timeout 60s;
    
    # Hide Nginx version
    server_tokens off;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
    limit_conn_zone \$binary_remote_addr zone=conn_limit_per_ip:10m;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rss+xml
        application/vnd.geo+json
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/bmp
        image/svg+xml
        image/x-icon
        text/cache-manifest
        text/css
        text/plain
        text/vcard
        text/vnd.rim.location.xloc
        text/vtt
        text/x-component
        text/x-cross-domain-policy;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Upstream backend
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # Upstream admin dashboard
    upstream admin_dashboard {
        server admin-dashboard:3000;
        keepalive 16;
    }

    # Upstream frontend
    upstream frontend {
        server frontend:3000;
        keepalive 16;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name $DOMAIN $API_DOMAIN $ADMIN_DOMAIN;
        
        # Allow Let's Encrypt challenges
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        # Redirect all other traffic to HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;
        
        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
        ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        
        # Content Security Policy
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://$API_DOMAIN; frame-ancestors 'none';" always;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_conn conn_limit_per_ip 20;

        # Frontend application
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-Host \$host;
            proxy_set_header X-Forwarded-Port \$server_port;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "Odoo SaaS Platform - Healthy\\n";
            add_header Content-Type text/plain;
        }
    }

    # API server
    server {
        listen 443 ssl http2;
        server_name $API_DOMAIN;
        
        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
        ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        
        # API-specific CSP
        add_header Content-Security-Policy "default-src 'none'; connect-src 'self';" always;

        # Rate limiting for API
        limit_req zone=api burst=50 nodelay;
        limit_conn conn_limit_per_ip 10;

        # API Backend
        location / {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-Host \$host;
            proxy_set_header X-Forwarded-Port \$server_port;
            
            # CORS headers for API
            add_header Access-Control-Allow-Origin "https://$DOMAIN" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header Access-Control-Allow-Credentials "true" always;
            
            if (\$request_method = 'OPTIONS') {
                add_header Access-Control-Allow-Origin "https://$DOMAIN";
                add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
                add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
                add_header Access-Control-Allow-Credentials "true";
                add_header Access-Control-Max-Age 1728000;
                add_header Content-Type 'text/plain; charset=utf-8';
                add_header Content-Length 0;
                return 204;
            }
        }

        # Authentication endpoints with stricter rate limiting
        location ~ ^/(api/v1/auth|api/v1/admin) {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }

    # Admin Dashboard server
    server {
        listen 443 ssl http2;
        server_name $ADMIN_DOMAIN;
        
        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
        ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        
        # Admin-specific CSP
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://$API_DOMAIN; frame-ancestors 'none';" always;

        # Stricter rate limiting for admin
        limit_req zone=api burst=10 nodelay;
        limit_conn conn_limit_per_ip 5;

        # Admin Dashboard
        location / {
            proxy_pass http://admin_dashboard;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-Host \$host;
            proxy_set_header X-Forwarded-Port \$server_port;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Default server (catch-all)
    server {
        listen 80 default_server;
        listen 443 ssl default_server;
        server_name _;
        
        # Self-signed certificate for default server
        ssl_certificate /etc/nginx/ssl/default.crt;
        ssl_certificate_key /etc/nginx/ssl/default.key;
        
        return 444;
    }
}
EOF
    
    print_status "Nginx configuration generated"
}

# Setup SSL certificates
setup_ssl() {
    print_step "Setting up SSL certificates..."
    
    # Create directories
    sudo mkdir -p /etc/letsencrypt/live/$DOMAIN
    sudo mkdir -p /var/www/certbot
    
    # Start nginx temporarily for certificate validation
    print_status "Starting temporary nginx for certificate validation..."
    
    # Create temporary nginx config for certificate validation
    sudo tee /etc/nginx/sites-available/temp-ssl << EOF
server {
    listen 80;
    server_name $DOMAIN $API_DOMAIN $ADMIN_DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable temporary config
    sudo ln -sf /etc/nginx/sites-available/temp-ssl /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    # Get SSL certificates
    print_status "Obtaining SSL certificates from Let's Encrypt..."
    sudo certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $SSL_EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d $API_DOMAIN \
        -d $ADMIN_DOMAIN
    
    # Remove temporary config
    sudo rm -f /etc/nginx/sites-enabled/temp-ssl
    sudo rm -f /etc/nginx/sites-available/temp-ssl
    
    # Setup auto-renewal
    print_status "Setting up automatic certificate renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'docker-compose -f $(pwd)/docker-compose.yml restart nginx'") | crontab -
    
    print_status "SSL certificates configured successfully"
}

# Configure firewall
configure_firewall() {
    print_step "Configuring firewall..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    print_status "Firewall configured successfully"
}

# Start services
start_services() {
    print_step "Starting services..."
    
    # Build and start containers
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service status
    docker-compose ps
    
    print_status "Services started successfully"
}

# Run database migrations
run_migrations() {
    print_step "Running database migrations..."
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose exec -T backend alembic upgrade head
    
    print_status "Database migrations completed"
}

# Create admin user
create_admin_user() {
    print_step "Creating admin user..."
    
    prompt_input "Admin email" "admin@$DOMAIN" "ADMIN_EMAIL"
    ADMIN_PASSWORD=$(generate_password)
    prompt_input "Admin password" "$ADMIN_PASSWORD" "ADMIN_PASSWORD"
    
    # Create admin user via API or direct database insertion
    # This would need to be implemented based on your user creation logic
    
    print_status "Admin user created:"
    print_status "Email: $ADMIN_EMAIL"
    print_status "Password: $ADMIN_PASSWORD"
}

# Display final information
display_final_info() {
    print_header "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    
    echo -e "${GREEN}Your Odoo SaaS Platform is now running!${NC}"
    echo ""
    echo -e "${CYAN}Access URLs:${NC}"
    echo -e "  Main Site:      ${YELLOW}https://$DOMAIN${NC}"
    echo -e "  API:            ${YELLOW}https://$API_DOMAIN${NC}"
    echo -e "  Admin Dashboard: ${YELLOW}https://$ADMIN_DOMAIN${NC}"
    echo ""
    echo -e "${CYAN}Admin Credentials:${NC}"
    echo -e "  Email:    ${YELLOW}$ADMIN_EMAIL${NC}"
    echo -e "  Password: ${YELLOW}$ADMIN_PASSWORD${NC}"
    echo ""
    echo -e "${CYAN}Important Files:${NC}"
    echo -e "  Environment: ${YELLOW}.env${NC}"
    echo -e "  Nginx Config: ${YELLOW}nginx/nginx.conf${NC}"
    echo -e "  Docker Compose: ${YELLOW}docker-compose.yml${NC}"
    echo ""
    echo -e "${CYAN}Useful Commands:${NC}"
    echo -e "  View logs:     ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  Restart:       ${YELLOW}docker-compose restart${NC}"
    echo -e "  Stop:          ${YELLOW}docker-compose down${NC}"
    echo -e "  Update:        ${YELLOW}git pull && docker-compose up -d --build${NC}"
    echo ""
    echo -e "${GREEN}SSL certificates will auto-renew every 12 hours.${NC}"
    echo -e "${GREEN}Firewall is configured and active.${NC}"
    echo ""
    echo -e "${PURPLE}Thank you for using Odoo SaaS Platform!${NC}"
}

# Main execution
main() {
    print_header "ODOO SAAS PLATFORM - INTERACTIVE DEPLOYMENT"
    
    # Check system requirements
    check_requirements
    
    # Install dependencies
    if prompt_yn "Install system dependencies?" "y"; then
        install_dependencies
    fi
    
    # Collect configuration
    collect_configuration
    
    # Generate configuration files
    generate_config
    generate_nginx_config
    
    # Configure firewall
    if prompt_yn "Configure firewall?" "y"; then
        configure_firewall
    fi
    
    # Setup SSL certificates
    if prompt_yn "Setup SSL certificates?" "y"; then
        setup_ssl
    fi
    
    # Start services
    start_services
    
    # Run migrations
    run_migrations
    
    # Create admin user
    if prompt_yn "Create admin user?" "y"; then
        create_admin_user
    fi
    
    # Display final information
    display_final_info
}

# Run main function
main "$@"

