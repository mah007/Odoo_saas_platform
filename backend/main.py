"""
Odoo SaaS Platform - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import logging
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, admin, tenants, billing, odoo_instances, monitoring, security, backup
from app.core.security import get_current_user
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Odoo SaaS Platform...")
    
    # Initialize database
    await init_db()
    logger.info("✅ Application started")
    
    yield
    
    logger.info("🛑 Shutting down Odoo SaaS Platform...")

# Create FastAPI app
app = FastAPI(
    title="Odoo SaaS Platform",
    description="Complete multi-tenant Odoo SaaS management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Static files
if os.path.exists("/app/uploads"):
    app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "odoo-saas-platform",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Odoo SaaS Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin"
    }

# Admin endpoint - simplified for now
@app.get("/admin")
async def admin_dashboard():
    """Admin dashboard endpoint"""
    return {
        "message": "Admin Dashboard",
        "status": "available",
        "redirect": "/admin.html"
    }

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(odoo_instances.router, prefix="/api/v1/odoo", tags=["Odoo Instances"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(security.router, prefix="/api/v1/security", tags=["Security"])
app.include_router(backup.router, prefix="/api/v1/backup", tags=["Backup"])

# Temporary API endpoints for testing
@app.get("/api/v1/admin/stats")
async def get_admin_stats():
    """Get admin statistics"""
    return {
        "stats": {
            "total_users": 0,
            "total_tenants": 0,
            "active_instances": 0,
            "total_revenue": 0
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

