"""
Tenant schemas for request/response validation
"""
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

class TenantCreate(BaseModel):
    name: str
    subdomain: str
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Subdomain must contain only lowercase letters, numbers, and hyphens')
        if len(v) < 3 or len(v) > 20:
            raise ValueError('Subdomain must be between 3 and 20 characters')
        return v

class TenantResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    status: str
    full_domain: str
    created_at: datetime
    
    class Config:
        from_attributes = True

