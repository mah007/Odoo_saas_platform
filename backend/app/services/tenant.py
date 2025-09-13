"""
Tenant management service
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.tenant import Tenant
from app.models.user import User
from app.models.odoo_instance import OdooInstance
from app.models.billing import Subscription
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.schemas.admin import TenantManagementResponse, TenantUpdateRequest

class TenantService:
    """Service for tenant management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tenant(self, tenant_data: TenantCreate, owner_id: int) -> Tenant:
        """Create a new tenant"""
        # Check if tenant name already exists for this user
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.name == tenant_data.name,
                Tenant.owner_id == owner_id
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("Tenant name already exists")
        
        # Create new tenant
        tenant = Tenant(
            name=tenant_data.name,
            description=tenant_data.description,
            owner_id=owner_id,
            max_instances=tenant_data.max_instances or 1,
            storage_limit_gb=tenant_data.storage_limit_gb or 10
        )
        
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID with related data"""
        result = await self.db.execute(
            select(Tenant)
            .options(selectinload(Tenant.owner))
            .options(selectinload(Tenant.instances))
            .where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_tenants(self, user_id: int) -> List[Tenant]:
        """Get all tenants for a user"""
        result = await self.db.execute(
            select(Tenant)
            .options(selectinload(Tenant.instances))
            .where(Tenant.owner_id == user_id)
            .order_by(Tenant.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_tenant(self, tenant_id: int, update_data: TenantUpdate, user_id: int) -> Optional[Tenant]:
        """Update tenant information"""
        # Check if user owns the tenant
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant or tenant.owner_id != user_id:
            return None
        
        # Remove None values
        update_dict = update_data.dict(exclude_unset=True)
        
        if not update_dict:
            return tenant
        
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(**update_dict, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return await self.get_tenant_by_id(tenant_id)
    
    async def delete_tenant(self, tenant_id: int, user_id: int) -> bool:
        """Delete tenant (only if user owns it and no active instances)"""
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant or tenant.owner_id != user_id:
            return False
        
        # Check if tenant has active instances
        instance_count = await self.db.execute(
            select(func.count(OdooInstance.id))
            .where(OdooInstance.tenant_id == tenant_id)
        )
        if instance_count.scalar() > 0:
            raise ValueError("Cannot delete tenant with active instances")
        
        result = await self.db.execute(
            delete(Tenant).where(Tenant.id == tenant_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_tenants_list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[TenantManagementResponse]:
        """Get paginated list of tenants for admin management"""
        query = select(
            Tenant,
            User.email.label('owner_email'),
            func.count(OdooInstance.id).label('instance_count')
        ).join(User).outerjoin(OdooInstance).group_by(Tenant.id, User.email)
        
        # Apply filters
        if search:
            query = query.where(
                Tenant.name.ilike(f"%{search}%") |
                Tenant.description.ilike(f"%{search}%") |
                User.email.ilike(f"%{search}%")
            )
        
        if status:
            query = query.where(Tenant.status == status)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        tenants_data = result.all()
        
        # Convert to response format
        tenants_list = []
        for tenant, owner_email, instance_count in tenants_data:
            # Get subscription info
            subscription_query = select(Subscription).where(
                Subscription.tenant_id == tenant.id
            ).order_by(Subscription.created_at.desc())
            subscription_result = await self.db.execute(subscription_query)
            subscription = subscription_result.scalar_one_or_none()
            
            tenants_list.append(TenantManagementResponse(
                id=tenant.id,
                name=tenant.name,
                owner_email=owner_email,
                status=tenant.status,
                instance_count=instance_count or 0,
                subscription_status=subscription.status if subscription else None,
                monthly_cost=subscription.plan.price if subscription and subscription.plan else 0,
                storage_used_gb=tenant.storage_used_gb or 0,
                created_at=tenant.created_at,
                last_activity=tenant.last_activity
            ))
        
        return tenants_list
    
    async def update_tenant_admin(self, tenant_id: int, update_data: TenantUpdateRequest) -> Optional[Tenant]:
        """Update tenant by admin"""
        update_dict = update_data.dict(exclude_unset=True)
        
        if not update_dict:
            return await self.get_tenant_by_id(tenant_id)
        
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(**update_dict, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return await self.get_tenant_by_id(tenant_id)
    
    async def get_tenant_stats(self, tenant_id: int) -> dict:
        """Get tenant statistics"""
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant:
            return {}
        
        # Get instance count and status
        instance_stats = await self.db.execute(
            select(
                func.count(OdooInstance.id).label('total'),
                func.count().filter(OdooInstance.status == 'running').label('running'),
                func.count().filter(OdooInstance.status == 'stopped').label('stopped'),
                func.count().filter(OdooInstance.status == 'error').label('error')
            ).where(OdooInstance.tenant_id == tenant_id)
        )
        stats = instance_stats.first()
        
        return {
            'total_instances': stats.total or 0,
            'running_instances': stats.running or 0,
            'stopped_instances': stats.stopped or 0,
            'error_instances': stats.error or 0,
            'storage_used_gb': tenant.storage_used_gb or 0,
            'storage_limit_gb': tenant.storage_limit_gb or 0,
            'max_instances': tenant.max_instances
        }
    
    async def update_tenant_activity(self, tenant_id: int) -> None:
        """Update tenant last activity timestamp"""
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(last_activity=datetime.utcnow())
        )
        await self.db.commit()
    
    async def check_tenant_limits(self, tenant_id: int) -> dict:
        """Check if tenant is within limits"""
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant:
            return {'valid': False, 'reason': 'Tenant not found'}
        
        # Check instance limit
        instance_count = await self.db.execute(
            select(func.count(OdooInstance.id))
            .where(OdooInstance.tenant_id == tenant_id)
        )
        current_instances = instance_count.scalar() or 0
        
        if current_instances >= tenant.max_instances:
            return {
                'valid': False, 
                'reason': f'Instance limit reached ({current_instances}/{tenant.max_instances})'
            }
        
        # Check storage limit
        if tenant.storage_used_gb and tenant.storage_limit_gb:
            if tenant.storage_used_gb >= tenant.storage_limit_gb:
                return {
                    'valid': False,
                    'reason': f'Storage limit reached ({tenant.storage_used_gb}/{tenant.storage_limit_gb} GB)'
                }
        
        return {'valid': True}

