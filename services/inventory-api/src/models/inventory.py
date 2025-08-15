"""
Inventory models for the Inventory API.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text, Boolean
from sqlalchemy.orm import relationship

from ..core.database import Base


class ItemType(str, Enum):
    """Item type enumeration."""
    VEHICLE = "vehicle"
    PART = "part"
    ACCESSORY = "accessory"
    SERVICE = "service"


class ItemStatus(str, Enum):
    """Item status enumeration."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class Item(Base):
    """Inventory item model."""
    
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(SQLEnum(ItemType), nullable=False)
    category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    
    # Pricing
    cost_price = Column(Numeric(10, 2), nullable=True)
    selling_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Inventory
    quantity_available = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)
    quantity_sold = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0, nullable=False)
    max_stock_level = Column(Integer, nullable=True)
    
    # Status
    status = Column(SQLEnum(ItemStatus), default=ItemStatus.AVAILABLE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Location
    warehouse_id = Column(String(100), nullable=True)
    location_code = Column(String(50), nullable=True)
    shelf_number = Column(String(20), nullable=True)
    
    # Specifications
    specifications = Column(Text, nullable=True)  # JSON string
    dimensions = Column(String(100), nullable=True)
    weight = Column(Numeric(8, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    inventory_movements = relationship("InventoryMovement", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Item(id={self.id}, item_id='{self.item_id}', name='{self.name}', type='{self.item_type}')>"


class MovementType(str, Enum):
    """Inventory movement type enumeration."""
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RESERVATION = "reservation"
    RELEASE = "release"


class InventoryMovement(Base):
    """Inventory movement model for tracking stock changes."""
    
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    movement_type = Column(SQLEnum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_id = Column(String(100), nullable=True)  # Order ID, PO ID, etc.
    reference_type = Column(String(50), nullable=True)  # order, purchase_order, etc.
    
    # Location
    from_warehouse = Column(String(100), nullable=True)
    to_warehouse = Column(String(100), nullable=True)
    from_location = Column(String(50), nullable=True)
    to_location = Column(String(50), nullable=True)
    
    # User tracking
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    item = relationship("Item", back_populates="inventory_movements")
    
    def __repr__(self) -> str:
        return f"<InventoryMovement(id={self.id}, item_id={self.item_id}, type='{self.movement_type}', quantity={self.quantity})>"


class Supplier(Base):
    """Supplier model."""
    
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Business details
    tax_id = Column(String(100), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, supplier_id='{self.supplier_id}', name='{self.name}')>"