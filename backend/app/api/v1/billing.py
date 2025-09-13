"""
Billing API endpoints for subscription management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.billing import BillingRecord

router = APIRouter()

@router.get("/records")
async def get_billing_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's billing records"""
    # Get user's tenants
    from app.models.tenant import Tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.owner_id == current_user.id)
    )
    tenants = tenant_result.scalars().all()
    tenant_ids = [t.id for t in tenants]
    
    if not tenant_ids:
        return []
    
    # Get billing records for user's tenants
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.tenant_id.in_(tenant_ids))
    )
    records = result.scalars().all()
    
    return [
        {
            "id": record.id,
            "amount": float(record.amount),
            "currency": record.currency,
            "status": record.status,
            "plan_name": record.plan_name,
            "billing_period_start": record.billing_period_start,
            "billing_period_end": record.billing_period_end,
            "created_at": record.created_at,
            "paid_at": record.paid_at
        }
        for record in records
    ]

@router.get("/plans")
async def get_billing_plans():
    """Get available billing plans"""
    return [
        {
            "id": "starter",
            "name": "Starter Plan",
            "price": 29.99,
            "currency": "USD",
            "features": [
                "Up to 10 users",
                "5GB storage",
                "Basic support",
                "Standard Odoo apps"
            ]
        },
        {
            "id": "professional",
            "name": "Professional Plan", 
            "price": 79.99,
            "currency": "USD",
            "features": [
                "Up to 50 users",
                "25GB storage",
                "Priority support",
                "All Odoo apps",
                "Custom domain"
            ]
        },
        {
            "id": "enterprise",
            "name": "Enterprise Plan",
            "price": 199.99,
            "currency": "USD",
            "features": [
                "Unlimited users",
                "100GB storage",
                "24/7 support",
                "All Odoo apps",
                "Custom domain",
                "Advanced integrations"
            ]
        }
    ]

