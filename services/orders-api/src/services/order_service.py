"""
Order service for business logic.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.order import Order, OrderItem, OrderStatus, PaymentStatus
from ..schemas.order import OrderCreate, OrderUpdate, OrderStatusUpdate, PaymentStatusUpdate

logger = structlog.get_logger()


class OrderService:
    """Service for order operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order."""
        logger.info("Creating new order", customer_id=order_data.customer_id, vehicle_id=order_data.vehicle_id)
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Calculate total amount
        total_amount = order_data.unit_price * order_data.quantity
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=order_data.customer_id,
            vehicle_id=order_data.vehicle_id,
            quantity=order_data.quantity,
            unit_price=order_data.unit_price,
            total_amount=total_amount,
            currency=order_data.currency,
            shipping_address=order_data.shipping_address,
            billing_address=order_data.billing_address,
            payment_method=order_data.payment_method,
            notes=order_data.notes,
            dealer_id=order_data.dealer_id,
        )
        
        self.db.add(order)
        await self.db.flush()  # Get the order ID
        
        # Create order items if provided
        if order_data.order_items:
            for item_data in order_data.order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    item_id=item_data.item_id,
                    item_name=item_data.item_name,
                    item_type=item_data.item_type,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.unit_price * item_data.quantity,
                )
                self.db.add(order_item)
                total_amount += order_item.total_price
        
        # Update total amount if items were added
        if order_data.order_items:
            order.total_amount = total_amount
        
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info("Order created successfully", order_id=order.id, order_number=order.order_number)
        return order
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        query = select(Order).options(selectinload(Order.order_items)).where(Order.id == order_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        query = select(Order).options(selectinload(Order.order_items)).where(Order.order_number == order_number)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_orders(
        self,
        customer_id: Optional[str] = None,
        dealer_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[List[Order], int]:
        """Get orders with filtering and pagination."""
        query = select(Order).options(selectinload(Order.order_items))
        
        # Apply filters
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if dealer_id:
            query = query.where(Order.dealer_id == dealer_id)
        if status:
            query = query.where(Order.order_status == status)
        
        # Get total count
        count_query = select(Order.id)
        if customer_id:
            count_query = count_query.where(Order.customer_id == customer_id)
        if dealer_id:
            count_query = count_query.where(Order.dealer_id == dealer_id)
        if status:
            count_query = count_query.where(Order.order_status == status)
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)
        query = query.order_by(Order.created_at.desc())
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return orders, total
    
    async def update_order(self, order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """Update order."""
        logger.info("Updating order", order_id=order_id)
        
        # Get existing order
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # Update fields
        update_data = order_data.dict(exclude_unset=True)
        if update_data:
            stmt = update(Order).where(Order.id == order_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info("Order updated successfully", order_id=order_id)
        
        return order
    
    async def update_order_status(self, order_id: int, status_data: OrderStatusUpdate) -> Optional[Order]:
        """Update order status."""
        logger.info("Updating order status", order_id=order_id, new_status=status_data.order_status)
        
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # Update status
        stmt = update(Order).where(Order.id == order_id).values(
            order_status=status_data.order_status,
            notes=status_data.notes or order.notes
        )
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info("Order status updated successfully", order_id=order_id, status=order.order_status)
        return order
    
    async def update_payment_status(self, order_id: int, payment_data: PaymentStatusUpdate) -> Optional[Order]:
        """Update payment status."""
        logger.info("Updating payment status", order_id=order_id, new_status=payment_data.payment_status)
        
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # Update payment status
        update_data = payment_data.dict(exclude_unset=True)
        stmt = update(Order).where(Order.id == order_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info("Payment status updated successfully", order_id=order_id, status=order.payment_status)
        return order
    
    async def delete_order(self, order_id: int) -> bool:
        """Delete order."""
        logger.info("Deleting order", order_id=order_id)
        
        order = await self.get_order(order_id)
        if not order:
            return False
        
        await self.db.delete(order)
        await self.db.commit()
        
        logger.info("Order deleted successfully", order_id=order_id)
        return True
    
    def _generate_order_number(self) -> str:
        """Generate unique order number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"ORD-{timestamp}-{unique_id}"