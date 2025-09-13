"""
Tenant model for multi-tenant architecture
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric
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
    description = Column(Text, nullable=True)
    
    # Owner information
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status and configuration
    status = Column(Enum(TenantStatus), default=TenantStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    
    # Resource limits
    max_instances = Column(Integer, default=1)
    max_users = Column(Integer, default=10)
    storage_limit_gb = Column(Integer, default=10)
    storage_used_gb = Column(Numeric(10, 2), default=0)
    
    # Activity tracking
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="tenants")
    instances = relationship("OdooInstance", back_populates="tenant")
    subscriptions = relationship("Subscription", back_populates="tenant")
    billing_records = relationship("BillingRecord", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant(name='{self.name}', owner_id={self.owner_id})>"

