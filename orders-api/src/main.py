from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api:8000")
VEHICLES_API_URL = os.getenv("VEHICLES_API_URL", "http://vehicles-api:8002")

app = FastAPI(
    title="Orders API",
    description="Car order management microservice",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# In-memory orders store (replace with database in production)
orders = {
    "ORD001": {
        "order_id": "ORD001",
        "customer_id": "3",
        "vehicle_vin": "VIN001",
        "dealer_id": "2",
        "status": "confirmed",
        "order_date": "2024-01-15T10:30:00Z",
        "delivery_date": "2024-02-15T10:00:00Z",
        "total_amount": 89999.99,
        "deposit_amount": 8999.99,
        "financing_approved": True,
        "trade_in_vehicle": None,
        "trade_in_value": 0.0,
        "additional_options": ["Extended Warranty", "Paint Protection"],
        "delivery_address": "789 Customer Rd, Customer Town, CT 13579",
        "notes": "Customer preferred delivery in the morning",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "ORD002": {
        "order_id": "ORD002",
        "customer_id": "3",
        "vehicle_vin": "VIN003",
        "dealer_id": "2",
        "status": "pending",
        "order_date": "2024-01-20T14:15:00Z",
        "delivery_date": None,
        "total_amount": 45999.99,
        "deposit_amount": 4599.99,
        "financing_approved": False,
        "trade_in_vehicle": "OLD123",
        "trade_in_value": 15000.0,
        "additional_options": ["Navigation Package"],
        "delivery_address": "789 Customer Rd, Customer Town, CT 13579",
        "notes": "Waiting for financing approval",
        "created_at": "2024-01-20T14:15:00Z",
        "updated_at": "2024-01-20T14:15:00Z"
    }
}

# Pydantic models
class Order(BaseModel):
    order_id: str
    customer_id: str
    vehicle_vin: str
    dealer_id: str
    status: str  # pending, confirmed, delivered, cancelled
    order_date: str
    delivery_date: Optional[str]
    total_amount: float
    deposit_amount: float
    financing_approved: bool
    trade_in_vehicle: Optional[str]
    trade_in_value: float
    additional_options: List[str]
    delivery_address: str
    notes: Optional[str]
    created_at: str
    updated_at: str

class OrderCreate(BaseModel):
    vehicle_vin: str
    dealer_id: str
    total_amount: float
    deposit_amount: float
    trade_in_vehicle: Optional[str] = None
    trade_in_value: float = 0.0
    additional_options: List[str] = []
    delivery_address: str
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    delivery_date: Optional[str] = None
    financing_approved: Optional[bool] = None
    trade_in_value: Optional[float] = None
    additional_options: Optional[List[str]] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

# Helper functions
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with auth service"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {credentials.credentials}"}
            response = await client.get(f"{AUTH_API_URL}/auth/verify", headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()
    except httpx.RequestError:
        # Fallback for development/testing
        logger.warning("Auth service unavailable, using fallback verification")
        return {"user_id": "1", "email": "admin@autocompany.com", "role": "admin"}

def generate_order_id() -> str:
    """Generate unique order ID"""
    return f"ORD{str(uuid.uuid4())[:8].upper()}"

# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "orders-api", "timestamp": datetime.utcnow()}

@app.get("/orders", response_model=List[Order])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    token_data: dict = Depends(verify_token)
):
    """List orders with optional filtering"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    filtered_orders = []
    
    for order in orders.values():
        # Apply role-based filtering
        if user_role == "customer" and order["customer_id"] != user_id:
            continue
        elif user_role == "dealer" and order["dealer_id"] != user_id:
            continue
        
        # Apply query filters
        if status and order["status"] != status:
            continue
        if customer_id and order["customer_id"] != customer_id:
            continue
        
        filtered_orders.append(order)
    
    result = filtered_orders[skip:skip + limit]
    order_list = [Order(**o) for o in result]
    
    logger.info(f"Listed {len(order_list)} orders for user {user_id}")
    return order_list

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, token_data: dict = Depends(verify_token)):
    """Get order by ID"""
    if order_id not in orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders[order_id]
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and order["customer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role == "dealer" and order["dealer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    logger.info(f"Retrieved order {order_id}")
    return Order(**order)

@app.post("/orders", response_model=Order)
async def create_order(
    order_data: OrderCreate,
    token_data: dict = Depends(verify_token)
):
    """Create a new order"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Only customers can create orders for themselves
    if user_role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create orders"
        )
    
    # TODO: Verify vehicle exists and is available via vehicles-api
    # For now, we'll skip this check
    
    order_id = generate_order_id()
    current_time = datetime.utcnow().isoformat() + "Z"
    
    new_order = {
        "order_id": order_id,
        "customer_id": user_id,
        "status": "pending",
        "order_date": current_time,
        "delivery_date": None,
        "financing_approved": False,
        "created_at": current_time,
        "updated_at": current_time,
        **order_data.dict()
    }
    
    orders[order_id] = new_order
    logger.info(f"Created new order {order_id} for customer {user_id}")
    
    return Order(**new_order)

@app.put("/orders/{order_id}", response_model=Order)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    token_data: dict = Depends(verify_token)
):
    """Update order"""
    if order_id not in orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders[order_id]
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and order["customer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role == "dealer" and order["dealer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_order = order.copy()
    update_data = order_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        updated_order[field] = value
    
    updated_order["updated_at"] = datetime.utcnow().isoformat() + "Z"
    orders[order_id] = updated_order
    
    logger.info(f"Updated order {order_id}")
    return Order(**updated_order)

@app.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    token_data: dict = Depends(verify_token)
):
    """Update order status (dealer or admin only)"""
    if order_id not in orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders[order_id]
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "dealer" and order["dealer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "dealer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or dealer access required"
        )
    
    valid_statuses = ["pending", "confirmed", "delivered", "cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    updated_order = order.copy()
    updated_order["status"] = status_update.status
    if status_update.notes:
        updated_order["notes"] = status_update.notes
    updated_order["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    orders[order_id] = updated_order
    
    logger.info(f"Updated order {order_id} status to {status_update.status}")
    return {"message": f"Order status updated to {status_update.status}"}

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str, token_data: dict = Depends(verify_token)):
    """Cancel order"""
    if order_id not in orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders[order_id]
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and order["customer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role == "dealer" and order["dealer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Only pending orders can be cancelled
    if order["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )
    
    updated_order = order.copy()
    updated_order["status"] = "cancelled"
    updated_order["updated_at"] = datetime.utcnow().isoformat() + "Z"
    orders[order_id] = updated_order
    
    logger.info(f"Cancelled order {order_id}")
    return {"message": f"Order {order_id} cancelled successfully"}

@app.get("/orders/customer/{customer_id}")
async def get_customer_orders(
    customer_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get orders for a specific customer"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and user_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "dealer", "customer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    customer_orders = [o for o in orders.values() if o["customer_id"] == customer_id]
    order_list = [Order(**o) for o in customer_orders]
    
    logger.info(f"Retrieved {len(order_list)} orders for customer {customer_id}")
    return {
        "orders": order_list,
        "total": len(order_list),
        "customer_id": customer_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)