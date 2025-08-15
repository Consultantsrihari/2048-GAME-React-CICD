"""
Orders API endpoints.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.order import OrderStatus
from ...schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderUpdate,
    PaymentStatusUpdate,
)
from ...services.order_service import OrderService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Create a new order."""
    logger.info("Creating new order", customer_id=order_data.customer_id)
    
    order_service = OrderService(db)
    order = await order_service.create_order(order_data)
    
    return OrderResponse.from_orm(order)


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    dealer_id: Optional[str] = Query(None, description="Filter by dealer ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
) -> OrderListResponse:
    """Get orders with filtering and pagination."""
    logger.info("Getting orders", customer_id=customer_id, dealer_id=dealer_id, status=status, page=page)
    
    order_service = OrderService(db)
    orders, total = await order_service.get_orders(
        customer_id=customer_id,
        dealer_id=dealer_id,
        status=status,
        page=page,
        size=size
    )
    
    # Calculate pagination info
    pages = (total + size - 1) // size
    
    return OrderListResponse(
        orders=[OrderResponse.from_orm(order) for order in orders],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Get order by ID."""
    logger.info("Getting order", order_id=order_id)
    
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.get("/orders/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Get order by order number."""
    logger.info("Getting order by number", order_number=order_number)
    
    order_service = OrderService(db)
    order = await order_service.get_order_by_number(order_number)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update order."""
    logger.info("Updating order", order_id=order_id)
    
    order_service = OrderService(db)
    order = await order_service.update_order(order_id, order_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update order status."""
    logger.info("Updating order status", order_id=order_id, status=status_data.order_status)
    
    order_service = OrderService(db)
    order = await order_service.update_order_status(order_id, status_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.patch("/orders/{order_id}/payment", response_model=OrderResponse)
async def update_payment_status(
    order_id: int,
    payment_data: PaymentStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update payment status."""
    logger.info("Updating payment status", order_id=order_id, status=payment_data.payment_status)
    
    order_service = OrderService(db)
    order = await order_service.update_payment_status(order_id, payment_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete order."""
    logger.info("Deleting order", order_id=order_id)
    
    order_service = OrderService(db)
    success = await order_service.delete_order(order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )