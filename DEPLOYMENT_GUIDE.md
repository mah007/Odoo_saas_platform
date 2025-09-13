# Odoo SaaS Platform - Comprehensive Deployment Guide

This guide provides a comprehensive overview of how to deploy the Odoo SaaS Platform in a production environment. It covers everything from initial setup to advanced configuration, security, and maintenance.

## Table of Contents

1.  **Introduction**
    *   Platform Overview
    *   Architecture
    *   Prerequisites
2.  **Initial Setup**
    *   Server Provisioning
    *   Domain Configuration
    *   Firewall Setup
3.  **Deployment**
    *   Cloning the Repository
    *   Configuring Environment Variables
    *   Running the Deployment Script
4.  **SSL/HTTPS Configuration**
    *   Setting up Let's Encrypt
    *   Automated Certificate Renewal
5.  **Security Hardening**
    *   Firewall Configuration
    *   Security Headers
    *   Rate Limiting
6.  **Backup & Restore**
    *   Automated Backups
    *   Manual Backups
    *   Restoration Procedures
7.  **Monitoring & Alerting**
    *   Prometheus Integration
    *   System Health Monitoring
    *   Alerting Configuration
8.  **Maintenance & Updates**
    *   Updating the Platform
    *   Troubleshooting
    *   Contribution Guide

---

## 1. Introduction

### Platform Overview

The Odoo SaaS Platform is a complete multi-tenant solution for managing Odoo instances. It provides a comprehensive admin dashboard, a user-friendly frontend, and a powerful backend API for automated deployment, management, and billing.

### Architecture

The platform is built on a modern, scalable architecture using Docker, FastAPI, React, and Nginx. It includes:

*   **Backend API**: FastAPI application for managing tenants, instances, billing, and security.
*   **Frontend**: React application for user registration, subscription management, and instance access.
*   **Admin Dashboard**: React application for platform administration, monitoring, and management.
*   **Nginx**: Reverse proxy for routing traffic, SSL termination, and security.
*   **PostgreSQL**: Database for storing platform data.
*   **Redis**: Caching and background tasks.
*   **Docker**: Containerization for all services.

### Prerequisites

*   A dedicated server with at least 4GB RAM, 2 CPU cores, and 50GB of storage.
*   Ubuntu 22.04 or a similar Linux distribution.
*   Docker and Docker Compose installed.
*   A registered domain name.

---

## 2. Initial Setup

### Server Provisioning

Provision a new server with the required specifications. Ensure you have root access and a non-root user with sudo privileges.

### Domain Configuration

Configure your domain's DNS records to point to your server's IP address. You will need at least three subdomains:

*   `host.yourdomain.com` (for the main frontend)
*   `api.yourdomain.com` (for the backend API)
*   `admin.yourdomain.com` (for the admin dashboard)

### Firewall Setup

Configure your firewall to allow traffic on the following ports:

*   `22/tcp` (SSH)
*   `80/tcp` (HTTP)
*   `443/tcp` (HTTPS)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 3. Deployment

### Cloning the Repository

Clone the Odoo SaaS Platform repository to your server:

```bash
git clone https://github.com/your-username/odoo-saas-platform.git
cd odoo-saas-platform
```

### Configuring Environment Variables

Create a `.env` file from the example and configure the required environment variables:

```bash
cp .env.example .env
nano .env
```

Key variables to configure:

*   `SECRET_KEY`: A strong, unique secret key.
*   `DATABASE_URL`: The connection string for your PostgreSQL database.
*   `STRIPE_API_KEY`: Your Stripe API key for billing.
*   `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`: Your AWS credentials for S3 backups.
*   `DOMAIN`: Your main domain name.

### Running the Deployment Script

The deployment script automates the entire setup process, including building Docker containers, running database migrations, and starting all services.

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 4. SSL/HTTPS Configuration

### Setting up Let's Encrypt

The platform includes a script for setting up SSL certificates with Let's Encrypt. Run the script to obtain and configure your certificates:

```bash
sudo ./scripts/setup-ssl.sh yourdomain.com api.yourdomain.com admin.yourdomain.com
```

### Automated Certificate Renewal

The script also sets up a cron job for automated certificate renewal. You can verify the cron job with:

```bash
sudo crontab -l
```

---

## 5. Security Hardening

### Firewall Configuration

Ensure your firewall is properly configured to restrict access to only necessary ports. The deployment script sets up basic firewall rules, but you may need to customize them for your environment.

### Security Headers

The Nginx configuration includes comprehensive security headers, such as HSTS, CSP, and X-Frame-Options. You can customize these headers in `nginx/nginx.conf`.

### Rate Limiting

Rate limiting is configured in Nginx to protect against brute-force attacks and DDoS. You can adjust the rate limits in `nginx/nginx.conf`.

---

## 6. Backup & Restore

### Automated Backups

The platform includes an automated backup system for both the database and files. Backups are stored locally and can be uploaded to S3. You can configure the backup schedule and retention policy in the admin dashboard.

### Manual Backups

You can create manual backups at any time from the admin dashboard or via the API.

### Restoration Procedures

Database and file restoration can be performed from the admin dashboard. Be cautious when restoring, as it will overwrite existing data.

---

## 7. Monitoring & Alerting

### Prometheus Integration

The platform exposes Prometheus metrics for monitoring system health and performance. You can configure your Prometheus server to scrape these metrics from the `/metrics` endpoint.

### System Health Monitoring

The admin dashboard provides real-time monitoring of CPU, memory, and disk usage. You can also view detailed performance metrics for the API and database.

### Alerting Configuration

Configure your alerting system (e.g., Alertmanager) to send notifications for critical system events, such as high resource usage or backup failures.

---

## 8. Maintenance & Updates

### Updating the Platform

To update the platform, pull the latest changes from the Git repository and run the deployment script again:

```bash
git pull origin main
./deploy.sh
```

### Troubleshooting

If you encounter any issues, check the logs for each service:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f admin-dashboard
docker-compose logs -f nginx
```

### Contribution Guide

We welcome contributions to the Odoo SaaS Platform! Please see the `CONTRIBUTING.md` file for more information on how to contribute.


