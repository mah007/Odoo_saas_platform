# Odoo SaaS Platform

🚀 **Complete Multi-Tenant Odoo SaaS Platform** with automated instance management, admin dashboard, billing system, and production-ready deployment.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)

## 🌟 Features

### 🎛️ **Admin Dashboard**
- Complete tenant management
- User administration and monitoring
- Billing and subscription management
- Automated Odoo instance provisioning
- System analytics and reporting
- Audit logging and compliance

### 👥 **User Portal**
- Self-service tenant registration
- Subscription management
- Odoo instance access and control
- Billing dashboard and invoices
- Support ticket system

### 🔧 **Backend Services**
- **FastAPI-based REST API** with async support
- **Multi-tenant architecture** with complete data isolation
- **Automated Odoo deployment** using Docker containers
- **Billing integration** with Stripe
- **Email notifications** and alerts
- **Comprehensive audit logging**
- **Rate limiting** and security features

### 🐳 **Odoo Integration**
- **Automated Odoo instance creation** per tenant
- **Docker-based Odoo deployment** with version management
- **Database isolation** per tenant
- **Backup and restore** functionality
- **Resource management** and monitoring
- **Subdomain routing** (tenant1.yourdomain.com)

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    NGINX REVERSE PROXY                      │
│                  (host.odoo-egypt.com)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   ADMIN     │ │  FRONTEND   │ │   BACKEND   │
│ DASHBOARD   │ │   (React)   │ │  (FastAPI)  │
│             │ │             │ │             │
└─────────────┘ └─────────────┘ └─────┬───────┘
                                      │
                              ┌───────┼───────┐
                              │       │       │
                              ▼       ▼       ▼
                        ┌─────────┐ ┌─────┐ ┌─────────┐
                        │POSTGRES │ │REDIS│ │ CELERY  │
                        │ Master  │ │     │ │ WORKER  │
                        │   DB    │ │     │ │         │
                        └─────────┘ └─────┘ └─────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   TENANT 1  │ │   TENANT 2  │ │   TENANT N  │
            │             │ │             │ │             │
            │ Odoo:8069   │ │ Odoo:8070   │ │ Odoo:807X   │
            │ DB: tenant1 │ │ DB: tenant2 │ │ DB: tenantN │
            └─────────────┘ └─────────────┘ └─────────────┘
```

## 🚀 **One-Click Deployment**

### **Prerequisites**
- Ubuntu 20.04+ or similar Linux distribution
- 4GB+ RAM, 2+ CPU cores
- Docker and Docker Compose
- Domain name pointing to your server

### **Quick Start**

```bash
# 1. Clone the repository
git clone https://github.com/mah007/Odoo_saas_platform.git
cd Odoo_saas_platform

# 2. Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

**That's it!** The script will:
- ✅ Install all dependencies
- ✅ Configure firewall and security
- ✅ Generate secure passwords
- ✅ Build and start all services
- ✅ Initialize database and create admin user
- ✅ Set up monitoring and logging

### **Access Your Platform**

After deployment completes:

- **Main Website**: `http://your-server-ip`
- **Admin Dashboard**: `http://your-server-ip/admin`
- **API Documentation**: `http://your-server-ip/docs`
- **Monitoring**: `http://your-server-ip:3001` (Grafana)

**Default Admin Credentials** (generated during deployment):
- Email: `admin@odoo-egypt.com`
- Password: `[shown in deployment output]`

## 🔧 **Manual Configuration**

### **Environment Variables**

Copy `.env.example` to `.env` and configure:

```bash
# Database
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://postgres:password@postgres:5432/odoo_saas_platform

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Domain
DOMAIN=your-domain.com
ALLOWED_ORIGINS=https://your-domain.com,http://your-domain.com

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Stripe (Optional)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### **Manual Deployment**

```bash
# Build and start services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 📊 **Multi-Tenant Features**

### **How Multi-Tenancy Works**

1. **Tenant Registration**: Users sign up and create tenant accounts
2. **Automatic Provisioning**: System creates isolated Odoo instances
3. **Database Isolation**: Each tenant gets separate PostgreSQL database
4. **Subdomain Routing**: `tenant1.yourdomain.com` → Odoo instance
5. **Resource Management**: CPU, memory, and storage limits per tenant
6. **Billing Integration**: Automatic subscription and payment processing

### **Tenant Management**

- **Create Tenant**: Automated Odoo instance provisioning
- **Manage Resources**: Set CPU, memory, storage limits
- **Monitor Usage**: Track resource consumption and costs
- **Backup/Restore**: Automated daily backups with retention
- **Version Management**: Upgrade Odoo versions per tenant

## 🔐 **Security Features**

- **JWT Authentication** with refresh tokens
- **Rate limiting** on API endpoints
- **Input validation** and sanitization
- **SQL injection** prevention
- **XSS protection** headers
- **CORS** configuration
- **Audit logging** for compliance
- **Encrypted passwords** with bcrypt
- **Security headers** (HSTS, CSP, etc.)

## 📈 **Monitoring & Analytics**

- **Prometheus** metrics collection
- **Grafana** dashboards and alerts
- **System health** monitoring
- **Resource usage** tracking
- **Billing analytics** and reporting
- **Audit logs** and compliance reporting

## 🛠️ **Development**

### **Local Development Setup**

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm install
npm start

# Admin dashboard development
cd admin-dashboard
npm install
npm start
```

### **API Documentation**

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### **Database Migrations**

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 🧪 **Testing**

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📦 **Production Deployment**

### **SSL/HTTPS Setup**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Scaling**

- **Horizontal scaling**: Multiple backend instances behind load balancer
- **Database scaling**: Read replicas and connection pooling
- **Caching**: Redis cluster for high availability
- **CDN**: Static asset delivery optimization

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

- **Documentation**: [Wiki](https://github.com/mah007/Odoo_saas_platform/wiki)
- **Issues**: [GitHub Issues](https://github.com/mah007/Odoo_saas_platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mah007/Odoo_saas_platform/discussions)

## 🎯 **Roadmap**

- [ ] Kubernetes deployment manifests
- [ ] Advanced billing features (usage-based pricing)
- [ ] Multi-region deployment support
- [ ] Advanced monitoring and alerting
- [ ] Mobile app for tenant management
- [ ] Marketplace for Odoo addons
- [ ] Advanced backup strategies (incremental, cross-region)
- [ ] Integration with cloud providers (AWS, GCP, Azure)

---

**⭐ Star this repository if you find it useful!**

Built with ❤️ for the Odoo community

