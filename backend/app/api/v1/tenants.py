"""
Tenants API endpoints for tenant management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.services.odoo_manager import create_odoo_instance
from app.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter()

@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant"""
    
    # Check if subdomain is available
    result = await db.execute(select(Tenant).where(Tenant.subdomain == tenant_data.subdomain))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subdomain already taken")
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        subdomain=tenant_data.subdomain,
        owner_id=current_user.id,
        status=TenantStatus.PENDING
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    # Create Odoo instance in background
    background_tasks.add_task(create_odoo_instance, tenant.id)
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        status=tenant.status,
        full_domain=tenant.full_domain,
        created_at=tenant.created_at
    )

@router.get("/", response_model=List[TenantResponse])
async def list_my_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List current user's tenants"""
    result = await db.execute(
        select(Tenant).where(Tenant.owner_id == current_user.id)
    )
    tenants = result.scalars().all()
    
    return [
        TenantResponse(
            id=tenant.id,
            name=tenant.name,
            subdomain=tenant.subdomain,
            status=tenant.status,
            full_domain=tenant.full_domain,
            created_at=tenant.created_at
        )
        for tenant in tenants
    ]

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tenant details"""
    result = await db.execute(
        select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.owner_id == current_user.id
        )
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        status=tenant.status,
        full_domain=tenant.full_domain,
        created_at=tenant.created_at
    )

