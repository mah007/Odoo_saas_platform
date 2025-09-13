"""
Odoo Instances API endpoints for instance management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.services.odoo_manager import start_instance, stop_instance, restart_instance

router = APIRouter()

@router.get("/")
async def list_instances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's Odoo instances"""
    # Get user's tenants
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.owner_id == current_user.id)
    )
    tenants = tenant_result.scalars().all()
    tenant_ids = [t.id for t in tenants]
    
    if not tenant_ids:
        return []
    
    # Get instances for user's tenants
    result = await db.execute(
        select(OdooInstance).where(OdooInstance.tenant_id.in_(tenant_ids))
    )
    instances = result.scalars().all()
    
    return [
        {
            "id": instance.id,
            "tenant_name": instance.tenant.name,
            "container_name": instance.container_name,
            "status": instance.status,
            "port": instance.port,
            "url": instance.url,
            "odoo_version": instance.odoo_version,
            "created_at": instance.created_at,
            "is_running": instance.is_running
        }
        for instance in instances
    ]

@router.post("/{instance_id}/start")
async def start_odoo_instance(
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
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Start instance in background
    background_tasks.add_task(start_instance, instance_id)
    
    return {"message": "Instance start initiated"}

@router.post("/{instance_id}/stop")
async def stop_odoo_instance(
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
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Stop instance in background
    background_tasks.add_task(stop_instance, instance_id)
    
    return {"message": "Instance stop initiated"}

@router.post("/{instance_id}/restart")
async def restart_odoo_instance(
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
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Restart instance in background
    background_tasks.add_task(restart_instance, instance_id)
    
    return {"message": "Instance restart initiated"}

