"""
Admin schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_tenants: int
    active_tenants: int
    total_instances: int
    running_instances: int
    total_revenue: Decimal
    monthly_revenue: Decimal
    storage_used_gb: float
    cpu_usage_percent: float
    memory_usage_percent: float

class SystemHealthResponse(BaseModel):
    status: str
    database_status: str
    redis_status: str
    docker_status: str
    disk_usage_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    active_connections: int
    last_check: datetime

class UserManagementResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    company: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    tenant_count: int
    instance_count: int
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None

class TenantManagementResponse(BaseModel):
    id: int
    name: str
    owner_email: str
    status: str
    instance_count: int
    subscription_status: Optional[str]
    monthly_cost: Decimal
    storage_used_gb: float
    created_at: datetime
    last_activity: Optional[datetime]
    
    class Config:
        from_attributes = True

class TenantUpdateRequest(BaseModel):
    status: Optional[str] = None
    max_instances: Optional[int] = None
    storage_limit_gb: Optional[int] = None

class InstanceManagementResponse(BaseModel):
    id: int
    tenant_name: str
    name: str
    status: str
    odoo_version: str
    url: Optional[str]
    cpu_usage: float
    memory_usage: float
    storage_used_gb: float
    uptime_hours: int
    last_backup: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class InstanceActionRequest(BaseModel):
    action: str = Field(..., pattern="^(start|stop|restart|backup|delete)$")
    force: bool = False

class BillingOverviewResponse(BaseModel):
    total_revenue: Decimal
    monthly_revenue: Decimal
    yearly_revenue: Decimal
    active_subscriptions: int
    cancelled_subscriptions: int
    trial_subscriptions: int
    average_revenue_per_user: Decimal
    churn_rate: float
    top_plans: List[Dict[str, Any]]

class AuditLogResponse(BaseModel):
    id: int
    user_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class SystemConfigResponse(BaseModel):
    key: str
    value: str
    description: Optional[str]
    is_sensitive: bool
    updated_at: datetime

class SystemConfigUpdate(BaseModel):
    value: str

class BackupManagementResponse(BaseModel):
    id: int
    instance_name: str
    tenant_name: str
    filename: str
    size_bytes: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MaintenanceScheduleResponse(BaseModel):
    id: int
    title: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: str
    affected_services: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MaintenanceScheduleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    affected_services: List[str] = []

