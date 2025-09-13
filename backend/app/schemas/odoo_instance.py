"""
Odoo Instance schemas for request/response validation
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class InstanceStatus(str, Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    UPDATING = "updating"
    DELETING = "deleting"
    ERROR = "error"

class InstanceType(str, Enum):
    COMMUNITY = "community"
    ENTERPRISE = "enterprise"

class OdooInstanceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    odoo_version: str = Field(default="17.0")
    instance_type: InstanceType = InstanceType.COMMUNITY
    database_name: str = Field(..., min_length=1, max_length=50)
    admin_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    admin_password: str = Field(..., min_length=8)
    modules: Optional[List[str]] = []
    custom_domain: Optional[str] = None

class OdooInstanceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    modules: Optional[List[str]] = None

class OdooInstanceResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    status: InstanceStatus
    odoo_version: str
    instance_type: InstanceType
    database_name: str
    admin_email: str
    url: Optional[str]
    custom_domain: Optional[str]
    port: int
    container_id: Optional[str]
    container_name: Optional[str]
    modules: List[str]
    cpu_limit: Optional[str]
    memory_limit: Optional[str]
    storage_size: Optional[str]
    last_backup: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InstanceStatsResponse(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: int
    network_out: int
    uptime: int
    active_users: int
    database_size: int

class InstanceBackupCreate(BaseModel):
    description: Optional[str] = None
    include_filestore: bool = True

class InstanceBackupResponse(BaseModel):
    id: int
    instance_id: int
    filename: str
    description: Optional[str]
    size_bytes: int
    include_filestore: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class InstanceRestoreRequest(BaseModel):
    backup_id: int
    restore_filestore: bool = True

class InstanceLogResponse(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str

class InstanceModuleInstall(BaseModel):
    modules: List[str] = Field(..., min_items=1)

class InstanceModuleResponse(BaseModel):
    name: str
    display_name: str
    version: str
    state: str
    description: Optional[str]
    depends: List[str]
    auto_install: bool

class InstanceConfigUpdate(BaseModel):
    config: Dict[str, Any] = Field(..., description="Odoo configuration parameters")

class InstanceScaleRequest(BaseModel):
    cpu_limit: Optional[str] = Field(None, description="CPU limit (e.g., '1.0', '500m')")
    memory_limit: Optional[str] = Field(None, description="Memory limit (e.g., '1Gi', '512Mi')")
    storage_size: Optional[str] = Field(None, description="Storage size (e.g., '10Gi', '5Gi')")

class InstanceHealthResponse(BaseModel):
    status: str
    database_connected: bool
    web_server_running: bool
    last_check: datetime
    response_time_ms: int
    error_message: Optional[str]

