"""
Billing API endpoints for subscription management with Stripe integration
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta
import stripe
import os
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.billing import BillingRecord, Subscription, PaymentMethod
from app.models.tenant import Tenant
from app.services.billing import BillingService

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()

class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    payment_method_id: str
    tenant_id: int

class UpdateSubscriptionRequest(BaseModel):
    plan_id: str

class CreatePaymentMethodRequest(BaseModel):
    stripe_payment_method_id: str
    is_default: bool = False

class CreateCheckoutSessionRequest(BaseModel):
    plan_id: str
    tenant_id: int
    success_url: str
    cancel_url: str

@router.get("/records")
async def get_billing_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's billing records with pagination"""
    # Get user's tenants
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.owner_id == current_user.id)
    )
    tenants = tenant_result.scalars().all()
    tenant_ids = [t.id for t in tenants]
    
    if not tenant_ids:
        return {"records": [], "total": 0}
    
    # Get billing records for user's tenants
    result = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id.in_(tenant_ids))
        .order_by(BillingRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id.in_(tenant_ids))
    )
    total = len(count_result.scalars().all())
    
    return {
        "records": [
            {
                "id": record.id,
                "tenant_id": record.tenant_id,
                "amount": record.amount,
                "currency": record.currency,
                "status": record.status,
                "plan_name": record.plan_name,
                "billing_period_start": record.billing_period_start,
                "billing_period_end": record.billing_period_end,
                "created_at": record.created_at,
                "paid_at": record.paid_at,
                "stripe_invoice_id": record.stripe_invoice_id
            }
            for record in records
        ],
        "total": total
    }

@router.get("/subscriptions")
async def get_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's active subscriptions"""
    # Get user's tenants
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.owner_id == current_user.id)
    )
    tenants = tenant_result.scalars().all()
    tenant_ids = [t.id for t in tenants]
    
    if not tenant_ids:
        return []
    
    # Get subscriptions for user's tenants
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id.in_(tenant_ids))
    )
    subscriptions = result.scalars().all()
    
    return [
        {
            "id": sub.id,
            "tenant_id": sub.tenant_id,
            "plan_id": sub.plan_id,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "created_at": sub.created_at
        }
        for sub in subscriptions
    ]

@router.post("/subscriptions")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new subscription"""
    # Verify tenant ownership
    tenant_result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == request.tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get plan details
    plans = await get_billing_plans()
    plan = next((p for p in plans if p["id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        # Create Stripe subscription
        stripe_subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{"price": plan["stripe_price_id"]}],
            default_payment_method=request.payment_method_id,
            expand=["latest_invoice.payment_intent"]
        )
        
        # Create subscription record
        subscription = Subscription(
            tenant_id=request.tenant_id,
            plan_id=request.plan_id,
            status=stripe_subscription.status,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
            stripe_subscription_id=stripe_subscription.id
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        # Create initial billing record
        billing_service = BillingService(db)
        await billing_service.create_billing_record_from_stripe_invoice(
            stripe_subscription.latest_invoice,
            request.tenant_id
        )
        
        return {
            "subscription_id": subscription.id,
            "stripe_subscription_id": stripe_subscription.id,
            "status": stripe_subscription.status,
            "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: int,
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update subscription plan"""
    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Verify tenant ownership
    tenant_result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == subscription.tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    if not tenant_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get new plan details
    plans = await get_billing_plans()
    new_plan = next((p for p in plans if p["id"] == request.plan_id), None)
    if not new_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        # Update Stripe subscription
        stripe_subscription = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{
                "id": stripe.Subscription.retrieve(subscription.stripe_subscription_id).items.data[0].id,
                "price": new_plan["stripe_price_id"]
            }],
            proration_behavior="create_prorations"
        )
        
        # Update local subscription
        subscription.plan_id = request.plan_id
        subscription.status = stripe_subscription.status
        await db.commit()
        
        return {"message": "Subscription updated successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    at_period_end: bool = True
):
    """Cancel subscription"""
    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Verify tenant ownership
    tenant_result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == subscription.tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    if not tenant_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if at_period_end:
            # Cancel at period end
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            subscription.cancel_at_period_end = True
        else:
            # Cancel immediately
            stripe_subscription = stripe.Subscription.delete(
                subscription.stripe_subscription_id
            )
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Subscription canceled successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-methods")
async def add_payment_method(
    request: CreatePaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add payment method"""
    try:
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            request.stripe_payment_method_id,
            customer=current_user.stripe_customer_id
        )
        
        # Get payment method details
        stripe_pm = stripe.PaymentMethod.retrieve(request.stripe_payment_method_id)
        
        # Create payment method record
        payment_method = PaymentMethod(
            user_id=current_user.id,
            stripe_payment_method_id=request.stripe_payment_method_id,
            type=stripe_pm.type,
            last_four=stripe_pm.card.last4 if stripe_pm.type == "card" else None,
            brand=stripe_pm.card.brand if stripe_pm.type == "card" else None,
            is_default=request.is_default
        )
        
        # If this is default, unset other defaults
        if request.is_default:
            await db.execute(
                select(PaymentMethod).where(
                    and_(PaymentMethod.user_id == current_user.id, PaymentMethod.is_default == True)
                ).update({"is_default": False})
            )
        
        db.add(payment_method)
        await db.commit()
        
        return {"message": "Payment method added successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's payment methods"""
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.user_id == current_user.id)
    )
    payment_methods = result.scalars().all()
    
    return [
        {
            "id": pm.id,
            "stripe_payment_method_id": pm.stripe_payment_method_id,
            "type": pm.type,
            "last_four": pm.last_four,
            "brand": pm.brand,
            "is_default": pm.is_default,
            "created_at": pm.created_at
        }
        for pm in payment_methods
    ]

@router.post("/checkout-session")
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create Stripe checkout session"""
    # Verify tenant ownership
    tenant_result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == request.tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get plan details
    plans = await get_billing_plans()
    plan = next((p for p in plans if p["id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": plan["stripe_price_id"],
                "quantity": 1
            }],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "tenant_id": request.tenant_id,
                "plan_id": request.plan_id
            }
        )
        
        return {"checkout_url": session.url, "session_id": session.id}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plans")
async def get_billing_plans():
    """Get available billing plans"""
    return [
        {
            "id": "starter",
            "name": "Starter Plan",
            "price": 2999,  # in cents
            "currency": "USD",
            "interval": "month",
            "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
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
            "price": 7999,  # in cents
            "currency": "USD",
            "interval": "month",
            "stripe_price_id": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID", "price_professional"),
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
            "price": 19999,  # in cents
            "currency": "USD",
            "interval": "month",
            "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise"),
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

@router.get("/usage/{tenant_id}")
async def get_usage_metrics(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get usage metrics for a tenant"""
    # Verify tenant ownership
    tenant_result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get usage metrics (implement based on your tracking needs)
    billing_service = BillingService(db)
    usage_metrics = await billing_service.get_usage_metrics(
        tenant_id, start_date, end_date
    )
    
    return usage_metrics

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: dict,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Handle Stripe webhooks"""
    # Verify webhook signature (implement signature verification)
    event_type = request.get("type")
    data = request.get("data", {}).get("object", {})
    
    billing_service = BillingService(db)
    
    if event_type == "invoice.payment_succeeded":
        await billing_service.handle_payment_succeeded(data)
    elif event_type == "invoice.payment_failed":
        await billing_service.handle_payment_failed(data)
    elif event_type == "customer.subscription.updated":
        await billing_service.handle_subscription_updated(data)
    elif event_type == "customer.subscription.deleted":
        await billing_service.handle_subscription_deleted(data)
    
    return {"status": "success"}

