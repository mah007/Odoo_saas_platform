"""
Odoo Instance model for managing Odoo containers
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class InstanceStatus(str, enum.Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UPDATING = "updating"
    DELETING = "deleting"

class OdooInstance(Base):
    __tablename__ = "odoo_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Container information
    container_id = Column(String(255), nullable=True)
    container_name = Column(String(255), unique=True, nullable=False)
    
    # Configuration
    odoo_version = Column(String(20), default="17.0")
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    admin_password = Column(String(255), nullable=False)
    
    # Status
    status = Column(Enum(InstanceStatus), default=InstanceStatus.CREATING)
    is_active = Column(Boolean, default=True)
    
    # Resource usage
    cpu_limit = Column(String(10), default="1.0")
    memory_limit = Column(String(10), default="1g")
    storage_used_mb = Column(Integer, default=0)
    
    # Configuration
    addons_path = Column(Text, nullable=True)
    config_data = Column(JSON, nullable=True)
    
    # Backup information
    last_backup_at = Column(DateTime(timezone=True), nullable=True)
    backup_schedule = Column(String(100), default="daily")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="instances")
    
    def __repr__(self):
        return f"<OdooInstance(container_name='{self.container_name}', status='{self.status}')>"
    
    @property
    def url(self):
        """Get Odoo instance URL"""
        return f"http://host.odoo-egypt.com:{self.port}"
    
    @property
    def is_running(self):
        """Check if instance is running"""
        return self.status == InstanceStatus.RUNNING

