"""
Tenant schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_instances: Optional[int] = Field(default=1, ge=1)
    storage_limit_gb: Optional[int] = Field(default=10, ge=1)

class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    max_instances: Optional[int] = Field(None, ge=1)
    storage_limit_gb: Optional[int] = Field(None, ge=1)

class TenantResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    status: str
    is_active: bool
    max_instances: int
    max_users: int
    storage_limit_gb: int
    storage_used_gb: Decimal
    last_activity: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TenantStats(BaseModel):
    total_instances: int
    running_instances: int
    stopped_instances: int
    error_instances: int
    storage_used_gb: Decimal
    storage_limit_gb: int
    max_instances: int

