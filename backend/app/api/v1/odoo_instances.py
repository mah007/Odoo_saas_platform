"""
Odoo Instances API endpoints for instance management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.services.tenant import TenantService
from app.services.admin_service import AdminService
from app.schemas.odoo_instance import (
    OdooInstanceCreate, OdooInstanceResponse, OdooInstanceUpdate,
    InstanceStatsResponse, InstanceBackupCreate, InstanceBackupResponse,
    InstanceRestoreRequest, InstanceLogResponse, InstanceModuleInstall,
    InstanceModuleResponse, InstanceConfigUpdate, InstanceScaleRequest,
    InstanceHealthResponse
)

router = APIRouter()

@router.post("/", response_model=OdooInstanceResponse)
async def create_instance(
    instance_data: OdooInstanceCreate,
    tenant_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new Odoo instance"""
    tenant_service = TenantService(db)
    
    # Check if user owns the tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant or tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check tenant limits
    limits_check = await tenant_service.check_tenant_limits(tenant_id)
    if not limits_check['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=limits_check['reason']
        )
    
    # TODO: Implement actual instance creation with Docker
    # For now, create a placeholder instance record
    instance = OdooInstance(
        tenant_id=tenant_id,
        container_name=f"odoo-{tenant_id}-{instance_data.name.lower().replace(' ', '-')}",
        odoo_version=instance_data.odoo_version,
        port=8069,  # TODO: Get next available port
        database_name=instance_data.database_name,
        admin_password=instance_data.admin_password,
        status="creating"
    )
    
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    
    # TODO: Add background task to create actual Docker container
    # background_tasks.add_task(create_odoo_container, instance.id)
    
    return OdooInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.container_name,
        description=instance_data.description,
        status=instance.status,
        odoo_version=instance.odoo_version,
        instance_type=instance_data.instance_type,
        database_name=instance.database_name,
        admin_email=instance_data.admin_email,
        url=instance.url,
        custom_domain=instance_data.custom_domain,
        port=instance.port,
        container_id=instance.container_id,
        container_name=instance.container_name,
        modules=instance_data.modules or [],
        cpu_limit=instance.cpu_limit,
        memory_limit=instance.memory_limit,
        storage_size=f"{instance.storage_used_mb}MB" if instance.storage_used_mb else "0MB",
        last_backup=instance.last_backup_at,
        created_at=instance.created_at,
        updated_at=instance.updated_at
    )

@router.get("/", response_model=List[OdooInstanceResponse])
async def list_instances(
    tenant_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's Odoo instances"""
    tenant_service = TenantService(db)
    
    if tenant_id:
        # Check if user owns the tenant
        tenant = await tenant_service.get_tenant_by_id(tenant_id)
        if not tenant or tenant.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Get instances for specific tenant
        result = await db.execute(
            select(OdooInstance).where(OdooInstance.tenant_id == tenant_id)
        )
        instances = result.scalars().all()
    else:
        # Get all instances for user's tenants
        user_tenants = await tenant_service.get_user_tenants(current_user.id)
        tenant_ids = [t.id for t in user_tenants]
        
        if not tenant_ids:
            return []
        
        result = await db.execute(
            select(OdooInstance).where(OdooInstance.tenant_id.in_(tenant_ids))
        )
        instances = result.scalars().all()
    
    return [
        OdooInstanceResponse(
            id=instance.id,
            tenant_id=instance.tenant_id,
            name=instance.container_name,
            description=None,  # TODO: Add description field to model
            status=instance.status,
            odoo_version=instance.odoo_version,
            instance_type="community",  # TODO: Add to model
            database_name=instance.database_name,
            admin_email="admin@example.com",  # TODO: Add to model
            url=instance.url,
            custom_domain=None,  # TODO: Add to model
            port=instance.port,
            container_id=instance.container_id,
            container_name=instance.container_name,
            modules=[],  # TODO: Add modules tracking
            cpu_limit=instance.cpu_limit,
            memory_limit=instance.memory_limit,
            storage_size=f"{instance.storage_used_mb}MB" if instance.storage_used_mb else "0MB",
            last_backup=instance.last_backup_at,
            created_at=instance.created_at,
            updated_at=instance.updated_at
        )
        for instance in instances
    ]

@router.get("/{instance_id}", response_model=OdooInstanceResponse)
async def get_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get instance details"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    return OdooInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.container_name,
        description=None,
        status=instance.status,
        odoo_version=instance.odoo_version,
        instance_type="community",
        database_name=instance.database_name,
        admin_email="admin@example.com",
        url=instance.url,
        custom_domain=None,
        port=instance.port,
        container_id=instance.container_id,
        container_name=instance.container_name,
        modules=[],
        cpu_limit=instance.cpu_limit,
        memory_limit=instance.memory_limit,
        storage_size=f"{instance.storage_used_mb}MB" if instance.storage_used_mb else "0MB",
        last_backup=instance.last_backup_at,
        created_at=instance.created_at,
        updated_at=instance.updated_at
    )

@router.put("/{instance_id}", response_model=OdooInstanceResponse)
async def update_instance(
    instance_id: int,
    instance_data: OdooInstanceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update instance configuration"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # Update instance fields
    update_data = instance_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(instance, field):
            setattr(instance, field, value)
    
    await db.commit()
    await db.refresh(instance)
    
    return OdooInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.container_name,
        description=instance_data.description,
        status=instance.status,
        odoo_version=instance.odoo_version,
        instance_type="community",
        database_name=instance.database_name,
        admin_email="admin@example.com",
        url=instance.url,
        custom_domain=instance_data.custom_domain,
        port=instance.port,
        container_id=instance.container_id,
        container_name=instance.container_name,
        modules=instance_data.modules or [],
        cpu_limit=instance.cpu_limit,
        memory_limit=instance.memory_limit,
        storage_size=f"{instance.storage_used_mb}MB" if instance.storage_used_mb else "0MB",
        last_backup=instance.last_backup_at,
        created_at=instance.created_at,
        updated_at=instance.updated_at
    )

@router.delete("/{instance_id}")
async def delete_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete instance"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Stop and remove Docker container
    
    # Delete instance record
    await db.delete(instance)
    await db.commit()
    
    return {"message": "Instance deleted successfully"}

# Instance control endpoints
@router.post("/{instance_id}/start")
async def start_instance(
    instance_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start Odoo instance"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Start Docker container
    # background_tasks.add_task(start_docker_container, instance_id)
    
    return {"message": "Instance start initiated"}

@router.post("/{instance_id}/stop")
async def stop_instance(
    instance_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop Odoo instance"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Stop Docker container
    # background_tasks.add_task(stop_docker_container, instance_id)
    
    return {"message": "Instance stop initiated"}

@router.post("/{instance_id}/restart")
async def restart_instance(
    instance_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Restart Odoo instance"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Restart Docker container
    # background_tasks.add_task(restart_docker_container, instance_id)
    
    return {"message": "Instance restart initiated"}

@router.get("/{instance_id}/stats", response_model=InstanceStatsResponse)
async def get_instance_stats(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get instance statistics"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Get real stats from Docker container
    return InstanceStatsResponse(
        cpu_usage=0.0,
        memory_usage=0.0,
        disk_usage=0.0,
        network_in=0,
        network_out=0,
        uptime=0,
        active_users=0,
        database_size=0
    )

@router.get("/{instance_id}/health", response_model=InstanceHealthResponse)
async def get_instance_health(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get instance health status"""
    # Get instance and verify ownership
    result = await db.execute(
        select(OdooInstance)
        .join(Tenant)
        .where(
            OdooInstance.id == instance_id,
            Tenant.owner_id == current_user.id
        )
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # TODO: Implement real health check
    return InstanceHealthResponse(
        status="healthy" if instance.status == "running" else "unhealthy",
        database_connected=True,
        web_server_running=instance.status == "running",
        last_check=instance.updated_at or instance.created_at,
        response_time_ms=100,
        error_message=None
    )

