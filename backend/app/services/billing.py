"""
Billing management service
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal
import stripe

from app.models.billing import SubscriptionPlan, Subscription, Payment, Invoice, Usage
from app.models.tenant import Tenant
from app.core.config import settings
from app.schemas.billing import (
    SubscriptionPlanCreate, SubscriptionPlanResponse,
    SubscriptionCreate, SubscriptionResponse,
    PaymentCreate, PaymentResponse,
    BillingStatsResponse
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class BillingService:
    """Service for billing and subscription management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Subscription Plans
    async def create_plan(self, plan_data: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create a new subscription plan"""
        plan = SubscriptionPlan(
            name=plan_data.name,
            description=plan_data.description,
            price=plan_data.price,
            currency=plan_data.currency,
            billing_interval=plan_data.billing_interval,
            max_instances=plan_data.max_instances,
            max_users=plan_data.max_users,
            storage_gb=plan_data.storage_gb,
            features=plan_data.features or []
        )
        
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        
        return plan
    
    async def get_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """Get all subscription plans"""
        query = select(SubscriptionPlan)
        if active_only:
            query = query.where(SubscriptionPlan.is_active == True)
        
        result = await self.db.execute(query.order_by(SubscriptionPlan.price))
        return result.scalars().all()
    
    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID"""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()
    
    # Subscriptions
    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription"""
        plan = await self.get_plan_by_id(subscription_data.plan_id)
        if not plan:
            raise ValueError("Subscription plan not found")
        
        # Check if tenant already has an active subscription
        existing = await self.db.execute(
            select(Subscription).where(
                Subscription.tenant_id == subscription_data.tenant_id,
                Subscription.status.in_(['active', 'trialing'])
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Tenant already has an active subscription")
        
        # Create Stripe subscription if payment method provided
        stripe_subscription_id = None
        if subscription_data.payment_method_id:
            try:
                # Create Stripe customer and subscription
                tenant = await self.db.execute(
                    select(Tenant).where(Tenant.id == subscription_data.tenant_id)
                )
                tenant = tenant.scalar_one()
                
                stripe_customer = stripe.Customer.create(
                    email=tenant.owner.email,
                    name=tenant.name,
                    payment_method=subscription_data.payment_method_id
                )
                
                stripe_subscription = stripe.Subscription.create(
                    customer=stripe_customer.id,
                    items=[{'price': plan.stripe_price_id}],
                    default_payment_method=subscription_data.payment_method_id
                )
                
                stripe_subscription_id = stripe_subscription.id
                
            except stripe.error.StripeError as e:
                raise ValueError(f"Payment processing failed: {str(e)}")
        
        # Create subscription
        subscription = Subscription(
            tenant_id=subscription_data.tenant_id,
            plan_id=subscription_data.plan_id,
            status='trialing' if not subscription_data.payment_method_id else 'active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            trial_end=datetime.utcnow() + timedelta(days=14) if not subscription_data.payment_method_id else None,
            stripe_subscription_id=stripe_subscription_id
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .options(selectinload(Subscription.tenant))
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_subscription(self, tenant_id: int) -> Optional[Subscription]:
        """Get active subscription for tenant"""
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_(['active', 'trialing', 'past_due'])
            )
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def cancel_subscription(self, subscription_id: int) -> bool:
        """Cancel subscription"""
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return False
        
        # Cancel in Stripe if exists
        if subscription.stripe_subscription_id:
            try:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
            except stripe.error.StripeError:
                pass  # Continue with local cancellation
        
        # Update local subscription
        await self.db.execute(
            update(Subscription)
            .where(Subscription.id == subscription_id)
            .values(status='cancelled', updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return True
    
    # Payments
    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a payment record"""
        subscription = await self.get_subscription_by_id(payment_data.subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        # Create Stripe payment intent
        stripe_payment_intent_id = None
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(payment_data.amount * 100),  # Convert to cents
                currency=payment_data.currency.lower(),
                payment_method=payment_data.payment_method_id,
                confirm=True,
                return_url="https://your-domain.com/return"
            )
            stripe_payment_intent_id = payment_intent.id
            
        except stripe.error.StripeError as e:
            # Create failed payment record
            payment = Payment(
                subscription_id=payment_data.subscription_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                status='failed',
                failure_reason=str(e)
            )
            self.db.add(payment)
            await self.db.commit()
            raise ValueError(f"Payment failed: {str(e)}")
        
        # Create successful payment record
        payment = Payment(
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status='completed',
            stripe_payment_intent_id=stripe_payment_intent_id
        )
        
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def get_subscription_payments(self, subscription_id: int) -> List[Payment]:
        """Get all payments for a subscription"""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.subscription_id == subscription_id)
            .order_by(Payment.created_at.desc())
        )
        return result.scalars().all()
    
    # Usage tracking
    async def record_usage(self, tenant_id: int, metric_name: str, value: int) -> Usage:
        """Record usage metric"""
        usage = Usage(
            tenant_id=tenant_id,
            metric_name=metric_name,
            value=value,
            recorded_at=datetime.utcnow()
        )
        
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        
        return usage
    
    async def get_tenant_usage(self, tenant_id: int, metric_name: str, start_date: datetime, end_date: datetime) -> List[Usage]:
        """Get usage data for tenant"""
        result = await self.db.execute(
            select(Usage)
            .where(
                Usage.tenant_id == tenant_id,
                Usage.metric_name == metric_name,
                Usage.recorded_at >= start_date,
                Usage.recorded_at <= end_date
            )
            .order_by(Usage.recorded_at)
        )
        return result.scalars().all()
    
    # Statistics
    async def get_billing_stats(self) -> BillingStatsResponse:
        """Get billing statistics"""
        # Total revenue
        total_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(Payment.status == 'completed')
        )
        total_revenue = total_revenue_result.scalar() or Decimal('0')
        
        # Monthly revenue
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(
                Payment.status == 'completed',
                Payment.created_at >= start_of_month
            )
        )
        monthly_revenue = monthly_revenue_result.scalar() or Decimal('0')
        
        # Active subscriptions
        active_subs_result = await self.db.execute(
            select(func.count(Subscription.id))
            .where(Subscription.status.in_(['active', 'trialing']))
        )
        active_subscriptions = active_subs_result.scalar() or 0
        
        # Total customers
        total_customers_result = await self.db.execute(
            select(func.count(func.distinct(Subscription.tenant_id)))
        )
        total_customers = total_customers_result.scalar() or 0
        
        # Calculate ARPU and churn rate
        arpu = total_revenue / total_customers if total_customers > 0 else Decimal('0')
        
        # Simple churn rate calculation (cancelled this month / total customers)
        cancelled_this_month = await self.db.execute(
            select(func.count(Subscription.id))
            .where(
                Subscription.status == 'cancelled',
                Subscription.updated_at >= start_of_month
            )
        )
        churn_rate = (cancelled_this_month.scalar() or 0) / total_customers if total_customers > 0 else 0.0
        
        return BillingStatsResponse(
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            active_subscriptions=active_subscriptions,
            total_customers=total_customers,
            churn_rate=churn_rate,
            average_revenue_per_user=arpu
        )

