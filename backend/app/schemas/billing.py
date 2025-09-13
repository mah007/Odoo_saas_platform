"""
Billing schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class SubscriptionPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    billing_interval: str = Field(default="monthly")  # monthly, yearly
    max_instances: int = Field(default=1, ge=1)
    max_users: int = Field(default=10, ge=1)
    storage_gb: int = Field(default=10, ge=1)
    features: Optional[List[str]] = []

class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    currency: str
    billing_interval: str
    max_instances: int
    max_users: int
    storage_gb: int
    features: List[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    tenant_id: int
    plan_id: int
    payment_method_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    plan_id: int
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime]
    stripe_subscription_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Related objects
    plan: SubscriptionPlanResponse
    
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    subscription_id: int
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method_id: str

class PaymentResponse(BaseModel):
    id: int
    subscription_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    stripe_payment_intent_id: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    subscription_id: int
    amount: Decimal
    currency: str
    status: str
    invoice_number: str
    due_date: datetime
    paid_at: Optional[datetime]
    stripe_invoice_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsageResponse(BaseModel):
    id: int
    tenant_id: int
    metric_name: str
    value: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class BillingStatsResponse(BaseModel):
    total_revenue: Decimal
    monthly_revenue: Decimal
    active_subscriptions: int
    total_customers: int
    churn_rate: float
    average_revenue_per_user: Decimal

