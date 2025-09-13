"""
Comprehensive admin service for platform management
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.models.billing import Subscription, Payment, SubscriptionPlan
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash
from app.core.config import settings
from app.schemas.admin import (
    AdminStatsResponse, SystemHealthResponse, UserManagementResponse,
    TenantManagementResponse, InstanceManagementResponse, BillingOverviewResponse,
    AuditLogResponse, AuditLogFilter
)

class AdminService:
    """Service for admin operations and platform management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_admin_stats(self) -> AdminStatsResponse:
        """Get comprehensive admin statistics"""
        # User statistics
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # Tenant statistics
        total_tenants_result = await self.db.execute(select(func.count(Tenant.id)))
        total_tenants = total_tenants_result.scalar() or 0
        
        active_tenants_result = await self.db.execute(
            select(func.count(Tenant.id)).where(Tenant.is_active == True)
        )
        active_tenants = active_tenants_result.scalar() or 0
        
        # Instance statistics
        total_instances_result = await self.db.execute(select(func.count(OdooInstance.id)))
        total_instances = total_instances_result.scalar() or 0
        
        running_instances_result = await self.db.execute(
            select(func.count(OdooInstance.id)).where(OdooInstance.status == 'running')
        )
        running_instances = running_instances_result.scalar() or 0
        
        # Revenue statistics
        total_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(Payment.status == 'completed')
        )
        total_revenue = total_revenue_result.scalar() or Decimal('0')
        
        # Monthly revenue
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == 'completed',
                Payment.created_at >= start_of_month
            )
        )
        monthly_revenue = monthly_revenue_result.scalar() or Decimal('0')
        
        # Storage and resource usage (placeholder values)
        storage_used_gb = 0.0
        cpu_usage_percent = 0.0
        memory_usage_percent = 0.0
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            total_instances=total_instances,
            running_instances=running_instances,
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            storage_used_gb=storage_used_gb,
            cpu_usage_percent=cpu_usage_percent,
            memory_usage_percent=memory_usage_percent
        )
    
    async def get_system_health(self) -> SystemHealthResponse:
        """Get system health status"""
        # Database status
        try:
            await self.db.execute(text("SELECT 1"))
            database_status = "healthy"
        except Exception:
            database_status = "error"
        
        # Redis status (placeholder)
        redis_status = "healthy"
        
        # Docker status (placeholder)
        docker_status = "healthy"
        
        return SystemHealthResponse(
            status="healthy" if database_status == "healthy" else "degraded",
            database_status=database_status,
            redis_status=redis_status,
            docker_status=docker_status,
            disk_usage_percent=50.0,
            memory_usage_percent=60.0,
            cpu_usage_percent=30.0,
            active_connections=10,
            last_check=datetime.utcnow()
        )
    
    async def get_users_management(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> List[UserManagementResponse]:
        """Get users for admin management"""
        query = select(User)
        
        # Apply filters
        if search:
            query = query.where(
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%") |
                User.company.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Convert to management response format
        users_list = []
        for user in users:
            # Get tenant count
            tenant_count_result = await self.db.execute(
                select(func.count(Tenant.id)).where(Tenant.owner_id == user.id)
            )
            tenant_count = tenant_count_result.scalar() or 0
            
            # Get instance count
            instance_count_result = await self.db.execute(
                select(func.count(OdooInstance.id))
                .join(Tenant)
                .where(Tenant.owner_id == user.id)
            )
            instance_count = instance_count_result.scalar() or 0
            
            users_list.append(UserManagementResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                company=user.company,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_admin=user.is_admin,
                tenant_count=tenant_count,
                instance_count=instance_count,
                last_login=user.last_login,
                created_at=user.created_at
            ))
        
        return users_list
    
    async def get_tenants_management(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[TenantManagementResponse]:
        """Get tenants for admin management"""
        query = select(Tenant).options(selectinload(Tenant.owner))
        
        # Apply filters
        if search:
            query = query.where(
                Tenant.name.ilike(f"%{search}%") |
                Tenant.description.ilike(f"%{search}%")
            )
        
        if status:
            query = query.where(Tenant.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Tenant.created_at.desc())
        
        result = await self.db.execute(query)
        tenants = result.scalars().all()
        
        # Convert to management response format
        tenants_list = []
        for tenant in tenants:
            # Get instance count
            instance_count_result = await self.db.execute(
                select(func.count(OdooInstance.id)).where(OdooInstance.tenant_id == tenant.id)
            )
            instance_count = instance_count_result.scalar() or 0
            
            # Get subscription info
            subscription_result = await self.db.execute(
                select(Subscription)
                .options(selectinload(Subscription.plan))
                .where(Subscription.tenant_id == tenant.id)
                .order_by(Subscription.created_at.desc())
            )
            subscription = subscription_result.scalar_one_or_none()
            
            tenants_list.append(TenantManagementResponse(
                id=tenant.id,
                name=tenant.name,
                owner_email=tenant.owner.email,
                status=tenant.status,
                instance_count=instance_count,
                subscription_status=subscription.status if subscription else None,
                monthly_cost=subscription.plan.price if subscription and subscription.plan else Decimal('0'),
                storage_used_gb=tenant.storage_used_gb or Decimal('0'),
                created_at=tenant.created_at,
                last_activity=tenant.last_activity
            ))
        
        return tenants_list
    
    async def get_instances_management(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[InstanceManagementResponse]:
        """Get instances for admin management"""
        query = select(OdooInstance).options(selectinload(OdooInstance.tenant))
        
        # Apply filters
        if search:
            query = query.where(
                OdooInstance.container_name.ilike(f"%{search}%") |
                OdooInstance.database_name.ilike(f"%{search}%")
            )
        
        if status:
            query = query.where(OdooInstance.status == status)
        
        query = query.offset(skip).limit(limit).order_by(OdooInstance.created_at.desc())
        
        result = await self.db.execute(query)
        instances = result.scalars().all()
        
        # Convert to management response format
        instances_list = []
        for instance in instances:
            # Calculate uptime
            uptime_hours = 0
            if instance.started_at:
                uptime_delta = datetime.utcnow() - instance.started_at
                uptime_hours = int(uptime_delta.total_seconds() / 3600)
            
            instances_list.append(InstanceManagementResponse(
                id=instance.id,
                tenant_name=instance.tenant.name,
                name=instance.container_name,
                status=instance.status,
                odoo_version=instance.odoo_version,
                url=instance.url,
                cpu_usage=0.0,  # Placeholder
                memory_usage=0.0,  # Placeholder
                storage_used_gb=instance.storage_used_mb / 1024 if instance.storage_used_mb else 0.0,
                uptime_hours=uptime_hours,
                last_backup=instance.last_backup_at,
                created_at=instance.created_at
            ))
        
        return instances_list
    
    async def get_billing_overview(self) -> BillingOverviewResponse:
        """Get billing overview for admin"""
        # Total revenue
        total_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(Payment.status == 'completed')
        )
        total_revenue = total_revenue_result.scalar() or Decimal('0')
        
        # Monthly revenue
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == 'completed',
                Payment.created_at >= start_of_month
            )
        )
        monthly_revenue = monthly_revenue_result.scalar() or Decimal('0')
        
        # Yearly revenue
        start_of_year = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        yearly_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == 'completed',
                Payment.created_at >= start_of_year
            )
        )
        yearly_revenue = yearly_revenue_result.scalar() or Decimal('0')
        
        # Subscription statistics
        active_subs_result = await self.db.execute(
            select(func.count(Subscription.id)).where(Subscription.status == 'active')
        )
        active_subscriptions = active_subs_result.scalar() or 0
        
        cancelled_subs_result = await self.db.execute(
            select(func.count(Subscription.id)).where(Subscription.status == 'cancelled')
        )
        cancelled_subscriptions = cancelled_subs_result.scalar() or 0
        
        trial_subs_result = await self.db.execute(
            select(func.count(Subscription.id)).where(Subscription.status == 'trialing')
        )
        trial_subscriptions = trial_subs_result.scalar() or 0
        
        # Calculate ARPU and churn rate
        total_customers = active_subscriptions + cancelled_subscriptions + trial_subscriptions
        arpu = total_revenue / total_customers if total_customers > 0 else Decimal('0')
        churn_rate = cancelled_subscriptions / total_customers if total_customers > 0 else 0.0
        
        # Top plans (placeholder)
        top_plans = []
        
        return BillingOverviewResponse(
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            yearly_revenue=yearly_revenue,
            active_subscriptions=active_subscriptions,
            cancelled_subscriptions=cancelled_subscriptions,
            trial_subscriptions=trial_subscriptions,
            average_revenue_per_user=arpu,
            churn_rate=churn_rate,
            top_plans=top_plans
        )
    
    async def log_admin_action(
        self, 
        admin_user_id: int, 
        action: str, 
        resource_type: str, 
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log admin action for audit trail"""
        audit_log = AuditLog(
            user_id=admin_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        return audit_log
    
    async def get_audit_logs(self, filters: AuditLogFilter) -> List[AuditLogResponse]:
        """Get audit logs with filtering"""
        query = select(AuditLog).options(selectinload(AuditLog.user))
        
        # Apply filters
        if filters.user_id:
            query = query.where(AuditLog.user_id == filters.user_id)
        
        if filters.action:
            query = query.where(AuditLog.action.ilike(f"%{filters.action}%"))
        
        if filters.resource_type:
            query = query.where(AuditLog.resource_type == filters.resource_type)
        
        if filters.start_date:
            query = query.where(AuditLog.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.where(AuditLog.created_at <= filters.end_date)
        
        query = query.offset(filters.offset).limit(filters.limit).order_by(AuditLog.created_at.desc())
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response format
        logs_list = []
        for log in logs:
            logs_list.append(AuditLogResponse(
                id=log.id,
                user_email=log.user.email if log.user else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=int(log.resource_id) if log.resource_id and log.resource_id.isdigit() else None,
                details=log.details or {},
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at
            ))
        
        return logs_list

