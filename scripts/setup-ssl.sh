#!/bin/bash

# SSL Setup Script for Odoo SaaS Platform
# This script sets up Let's Encrypt SSL certificates for the platform

set -e

# Configuration
DOMAIN="host.odoo-egypt.com"
API_DOMAIN="api.host.odoo-egypt.com"
ADMIN_DOMAIN="admin.host.odoo-egypt.com"
EMAIL="admin@odoo-egypt.com"
NGINX_SSL_DIR="/etc/nginx/ssl"
CERTBOT_DIR="/etc/letsencrypt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
fi

# Check if domains are provided
if [ $# -eq 3 ]; then
    DOMAIN=$1
    API_DOMAIN=$2
    ADMIN_DOMAIN=$3
    log "Using provided domains: $DOMAIN, $API_DOMAIN, $ADMIN_DOMAIN"
fi

# Install certbot if not present
install_certbot() {
    log "Installing Certbot..."
    
    if command -v certbot &> /dev/null; then
        log "Certbot is already installed"
        return
    fi
    
    # Install snapd if not present
    if ! command -v snap &> /dev/null; then
        apt update
        apt install -y snapd
    fi
    
    # Install certbot via snap
    snap install core; snap refresh core
    snap install --classic certbot
    
    # Create symlink
    ln -sf /snap/bin/certbot /usr/bin/certbot
    
    log "Certbot installed successfully"
}

# Create SSL directory
create_ssl_directory() {
    log "Creating SSL directory..."
    mkdir -p $NGINX_SSL_DIR
    mkdir -p /var/www/certbot
    chmod 755 /var/www/certbot
}

# Generate self-signed certificates for initial setup
generate_self_signed_certs() {
    log "Generating self-signed certificates for initial setup..."
    
    # Main domain certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $NGINX_SSL_DIR/privkey.pem \
        -out $NGINX_SSL_DIR/fullchain.pem \
        -subj "/C=EG/ST=Cairo/L=Cairo/O=Odoo Egypt/OU=IT Department/CN=$DOMAIN"
    
    # Chain certificate (copy of fullchain for compatibility)
    cp $NGINX_SSL_DIR/fullchain.pem $NGINX_SSL_DIR/chain.pem
    
    # Default certificate for catch-all server
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $NGINX_SSL_DIR/default.key \
        -out $NGINX_SSL_DIR/default.crt \
        -subj "/C=EG/ST=Cairo/L=Cairo/O=Default/OU=IT/CN=default"
    
    log "Self-signed certificates generated"
}

# Check DNS resolution
check_dns() {
    log "Checking DNS resolution for domains..."
    
    for domain in $DOMAIN $API_DOMAIN $ADMIN_DOMAIN; do
        if ! nslookup $domain > /dev/null 2>&1; then
            warn "DNS resolution failed for $domain"
            warn "Please ensure the domain points to this server's IP address"
        else
            log "DNS resolution OK for $domain"
        fi
    done
}

# Test Nginx configuration
test_nginx_config() {
    log "Testing Nginx configuration..."
    
    if nginx -t; then
        log "Nginx configuration is valid"
    else
        error "Nginx configuration test failed"
    fi
}

# Obtain Let's Encrypt certificates
obtain_letsencrypt_certs() {
    log "Obtaining Let's Encrypt certificates..."
    
    # Stop nginx temporarily
    systemctl stop nginx || docker-compose stop nginx || warn "Could not stop nginx"
    
    # Obtain certificates for all domains
    certbot certonly \
        --standalone \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --expand \
        -d $DOMAIN \
        -d $API_DOMAIN \
        -d $ADMIN_DOMAIN
    
    if [ $? -eq 0 ]; then
        log "Let's Encrypt certificates obtained successfully"
        
        # Copy certificates to nginx directory
        cp $CERTBOT_DIR/live/$DOMAIN/fullchain.pem $NGINX_SSL_DIR/
        cp $CERTBOT_DIR/live/$DOMAIN/privkey.pem $NGINX_SSL_DIR/
        cp $CERTBOT_DIR/live/$DOMAIN/chain.pem $NGINX_SSL_DIR/
        
        # Set proper permissions
        chmod 644 $NGINX_SSL_DIR/fullchain.pem
        chmod 644 $NGINX_SSL_DIR/chain.pem
        chmod 600 $NGINX_SSL_DIR/privkey.pem
        
        log "Certificates copied to Nginx directory"
    else
        warn "Let's Encrypt certificate generation failed, using self-signed certificates"
        generate_self_signed_certs
    fi
    
    # Start nginx
    systemctl start nginx || docker-compose start nginx || warn "Could not start nginx"
}

# Setup certificate renewal
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash

# Renew certificates
certbot renew --quiet

# Copy renewed certificates
if [ -f /etc/letsencrypt/live/host.odoo-egypt.com/fullchain.pem ]; then
    cp /etc/letsencrypt/live/host.odoo-egypt.com/fullchain.pem /etc/nginx/ssl/
    cp /etc/letsencrypt/live/host.odoo-egypt.com/privkey.pem /etc/nginx/ssl/
    cp /etc/letsencrypt/live/host.odoo-egypt.com/chain.pem /etc/nginx/ssl/
    
    # Set permissions
    chmod 644 /etc/nginx/ssl/fullchain.pem
    chmod 644 /etc/nginx/ssl/chain.pem
    chmod 600 /etc/nginx/ssl/privkey.pem
    
    # Reload nginx
    systemctl reload nginx || docker-compose exec nginx nginx -s reload
fi
EOF
    
    chmod +x /usr/local/bin/renew-ssl.sh
    
    # Add cron job for renewal (runs twice daily)
    (crontab -l 2>/dev/null; echo "0 */12 * * * /usr/local/bin/renew-ssl.sh") | crontab -
    
    log "Automatic renewal configured"
}

# Setup firewall rules
setup_firewall() {
    log "Setting up firewall rules..."
    
    if command -v ufw &> /dev/null; then
        # Allow HTTP and HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Allow SSH (be careful!)
        ufw allow 22/tcp
        
        log "Firewall rules configured"
    else
        warn "UFW not found, please configure firewall manually"
        warn "Ensure ports 80 and 443 are open"
    fi
}

# Verify SSL setup
verify_ssl() {
    log "Verifying SSL setup..."
    
    # Test SSL certificate
    for domain in $DOMAIN $API_DOMAIN $ADMIN_DOMAIN; do
        log "Testing SSL for $domain..."
        
        if openssl s_client -connect $domain:443 -servername $domain < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
            log "SSL verification successful for $domain"
        else
            warn "SSL verification failed for $domain"
        fi
    done
}

# Main execution
main() {
    log "Starting SSL setup for Odoo SaaS Platform..."
    
    # Check prerequisites
    check_dns
    
    # Install certbot
    install_certbot
    
    # Create directories
    create_ssl_directory
    
    # Generate initial self-signed certificates
    generate_self_signed_certs
    
    # Test nginx configuration
    test_nginx_config
    
    # Setup firewall
    setup_firewall
    
    # Obtain Let's Encrypt certificates
    obtain_letsencrypt_certs
    
    # Setup automatic renewal
    setup_renewal
    
    # Verify SSL setup
    verify_ssl
    
    log "SSL setup completed successfully!"
    log ""
    log "Your domains are now secured with SSL:"
    log "  - https://$DOMAIN"
    log "  - https://$API_DOMAIN"
    log "  - https://$ADMIN_DOMAIN"
    log ""
    log "Certificate renewal is configured to run automatically."
    log "You can manually renew certificates with: certbot renew"
}

# Show usage
usage() {
    echo "Usage: $0 [main_domain] [api_domain] [admin_domain]"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 yourdomain.com api.yourdomain.com admin.yourdomain.com"
    echo ""
    echo "If no domains are provided, default domains will be used:"
    echo "  - $DOMAIN"
    echo "  - $API_DOMAIN"
    echo "  - $ADMIN_DOMAIN"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac

