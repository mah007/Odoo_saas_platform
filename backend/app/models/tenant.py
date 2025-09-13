"""
Tenant model for multi-tenant architecture
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class TenantStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(255), nullable=True)
    
    # Owner information
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status and configuration
    status = Column(Enum(TenantStatus), default=TenantStatus.PENDING)
    is_active = Column(Boolean, default=True)
    
    # Odoo configuration
    odoo_version = Column(String(20), default="17.0")
    odoo_port = Column(Integer, nullable=True)
    odoo_database = Column(String(100), nullable=True)
    odoo_admin_password = Column(String(255), nullable=True)
    
    # Resource limits
    max_users = Column(Integer, default=10)
    storage_limit_gb = Column(Integer, default=5)
    
    # Billing information
    plan_id = Column(String(100), nullable=True)
    subscription_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="tenants")
    odoo_instance = relationship("OdooInstance", back_populates="tenant", uselist=False)
    billing_records = relationship("BillingRecord", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant(name='{self.name}', subdomain='{self.subdomain}')>"
    
    @property
    def full_domain(self):
        """Get full domain for tenant"""
        return f"{self.subdomain}.host.odoo-egypt.com"

