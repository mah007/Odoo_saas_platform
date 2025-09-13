"""
Configuration settings for Odoo SaaS Platform
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic settings
    APP_NAME: str = "Odoo SaaS Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/odoo_saas_platform"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://host.odoo-egypt.com",
        "http://host.odoo-egypt.com"
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "host.odoo-egypt.com",
        "*"
    ]
    
    # Admin
    ADMIN_EMAIL: str = "admin@odoo-egypt.com"
    ADMIN_PASSWORD: str = "admin123"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@odoo-egypt.com"
    SMTP_FROM_NAME: str = "Odoo SaaS Platform"
    
    # Odoo
    ODOO_DOCKER_IMAGE: str = "odoo:17.0"
    ODOO_BASE_PORT: int = 8069
    ODOO_INSTANCES_PATH: str = "/app/odoo-instances"
    
    # Billing
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    UPLOAD_PATH: str = "/app/uploads"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

