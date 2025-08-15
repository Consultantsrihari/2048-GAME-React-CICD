"""
Pydantic schemas for Orders API.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from ..models.order import OrderStatus, PaymentStatus


class OrderItemBase(BaseModel):
    """Base order item schema."""
    item_id: str = Field(..., description="Item identifier")
    item_name: str = Field(..., description="Item name")
    item_type: str = Field(..., description="Item type (accessory, service, etc.)")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")


class OrderItemCreate(OrderItemBase):
    """Schema for creating order items."""
    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item responses."""
    id: int
    total_price: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order schema."""
    customer_id: str = Field(..., description="Customer identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    currency: str = Field("USD", description="Currency code")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    billing_address: Optional[str] = Field(None, description="Billing address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, description="Order notes")
    dealer_id: Optional[str] = Field(None, description="Dealer identifier")


class OrderCreate(OrderBase):
    """Schema for creating orders."""
    order_items: Optional[List[OrderItemCreate]] = Field(default_factory=list, description="Order items")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        if v and len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()


class OrderUpdate(BaseModel):
    """Schema for updating orders."""
    order_status: Optional[OrderStatus] = Field(None, description="Order status")
    payment_status: Optional[PaymentStatus] = Field(None, description="Payment status")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    billing_address: Optional[str] = Field(None, description="Billing address")
    notes: Optional[str] = Field(None, description="Order notes")


class OrderResponse(OrderBase):
    """Schema for order responses."""
    id: int
    order_number: str
    total_amount: Decimal
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_intent_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for order list responses."""
    orders: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    order_status: OrderStatus = Field(..., description="New order status")
    notes: Optional[str] = Field(None, description="Status change notes")


class PaymentStatusUpdate(BaseModel):
    """Schema for updating payment status."""
    payment_status: PaymentStatus = Field(..., description="New payment status")
    payment_intent_id: Optional[str] = Field(None, description="Payment intent ID")
    notes: Optional[str] = Field(None, description="Payment status notes")