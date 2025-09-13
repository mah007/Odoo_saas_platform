"""
Tenants API endpoints for tenant management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.tenant import TenantService
from app.services.admin_service import AdminService
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate, TenantStats

router = APIRouter()

@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant"""
    tenant_service = TenantService(db)
    
    try:
        # Create tenant
        tenant = await tenant_service.create_tenant(tenant_data, current_user.id)
        
        # TODO: Add background task to create Odoo instance
        # background_tasks.add_task(create_odoo_instance, tenant.id)
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            description=tenant.description,
            owner_id=tenant.owner_id,
            status=tenant.status,
            is_active=tenant.is_active,
            max_instances=tenant.max_instances,
            max_users=tenant.max_users,
            storage_limit_gb=tenant.storage_limit_gb,
            storage_used_gb=tenant.storage_used_gb,
            last_activity=tenant.last_activity,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[TenantResponse])
async def list_my_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List current user's tenants"""
    tenant_service = TenantService(db)
    tenants = await tenant_service.get_user_tenants(current_user.id)
    
    return [
        TenantResponse(
            id=tenant.id,
            name=tenant.name,
            description=tenant.description,
            owner_id=tenant.owner_id,
            status=tenant.status,
            is_active=tenant.is_active,
            max_instances=tenant.max_instances,
            max_users=tenant.max_users,
            storage_limit_gb=tenant.storage_limit_gb,
            storage_used_gb=tenant.storage_used_gb,
            last_activity=tenant.last_activity,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
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
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    
    if not tenant or tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        description=tenant.description,
        owner_id=tenant.owner_id,
        status=tenant.status,
        is_active=tenant.is_active,
        max_instances=tenant.max_instances,
        max_users=tenant.max_users,
        storage_limit_gb=tenant.storage_limit_gb,
        storage_used_gb=tenant.storage_used_gb,
        last_activity=tenant.last_activity,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tenant information"""
    tenant_service = TenantService(db)
    
    tenant = await tenant_service.update_tenant(tenant_id, tenant_data, current_user.id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        description=tenant.description,
        owner_id=tenant.owner_id,
        status=tenant.status,
        is_active=tenant.is_active,
        max_instances=tenant.max_instances,
        max_users=tenant.max_users,
        storage_limit_gb=tenant.storage_limit_gb,
        storage_used_gb=tenant.storage_used_gb,
        last_activity=tenant.last_activity,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete tenant"""
    tenant_service = TenantService(db)
    
    try:
        success = await tenant_service.delete_tenant(tenant_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return {"message": "Tenant deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tenant statistics"""
    tenant_service = TenantService(db)
    
    # Check if user owns the tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant or tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    stats = await tenant_service.get_tenant_stats(tenant_id)
    
    return TenantStats(
        total_instances=stats['total_instances'],
        running_instances=stats['running_instances'],
        stopped_instances=stats['stopped_instances'],
        error_instances=stats['error_instances'],
        storage_used_gb=stats['storage_used_gb'],
        storage_limit_gb=stats['storage_limit_gb'],
        max_instances=stats['max_instances']
    )

@router.post("/{tenant_id}/check-limits")
async def check_tenant_limits(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if tenant is within limits"""
    tenant_service = TenantService(db)
    
    # Check if user owns the tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant or tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    limits_check = await tenant_service.check_tenant_limits(tenant_id)
    
    return limits_check

# Admin endpoints
@router.get("/admin/all", response_model=List[dict])
async def list_all_tenants_admin(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tenants (admin only)"""
    admin_service = AdminService(db)
    
    tenants = await admin_service.get_tenants_management(
        skip=skip,
        limit=limit,
        search=search,
        status=status
    )
    
    return [tenant.dict() for tenant in tenants]

@router.put("/admin/{tenant_id}")
async def update_tenant_admin(
    tenant_id: int,
    update_data: dict,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tenant (admin only)"""
    from app.schemas.admin import TenantUpdateRequest
    
    admin_service = AdminService(db)
    tenant_service = TenantService(db)
    
    # Log admin action
    await admin_service.log_admin_action(
        admin_user_id=current_admin.id,
        action="update_tenant",
        resource_type="tenant",
        resource_id=tenant_id,
        details=update_data
    )
    
    update_request = TenantUpdateRequest(**update_data)
    tenant = await tenant_service.update_tenant_admin(tenant_id, update_request)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return {"message": "Tenant updated successfully"}

@router.post("/{tenant_id}/activity")
async def update_tenant_activity(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tenant last activity timestamp"""
    tenant_service = TenantService(db)
    
    # Check if user owns the tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant or tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    await tenant_service.update_tenant_activity(tenant_id)
    
    return {"message": "Activity updated successfully"}

