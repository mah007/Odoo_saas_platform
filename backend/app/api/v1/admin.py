"""
Admin API endpoints for system management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.models.billing import BillingRecord

router = APIRouter()

@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Get total counts
    total_users = await db.scalar(select(func.count(User.id)))
    total_tenants = await db.scalar(select(func.count(Tenant.id)))
    active_instances = await db.scalar(
        select(func.count(OdooInstance.id)).where(OdooInstance.is_active == True)
    )
    total_revenue = await db.scalar(
        select(func.sum(BillingRecord.amount)).where(BillingRecord.status == "paid")
    ) or 0
    
    return {
        "total_users": total_users,
        "total_tenants": total_tenants,
        "active_instances": active_instances,
        "total_revenue": float(total_revenue),
        "admin_user": current_user.email
    }

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company": user.company,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.get("/tenants")
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tenants"""
    result = await db.execute(
        select(Tenant).offset(skip).limit(limit)
    )
    tenants = result.scalars().all()
    
    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "status": tenant.status,
            "owner_email": tenant.owner.email if tenant.owner else None,
            "created_at": tenant.created_at,
            "full_domain": tenant.full_domain
        }
        for tenant in tenants
    ]

