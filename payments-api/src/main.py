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

app = FastAPI(
    title="Payments API",
    description="Transaction processing microservice",
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

# In-memory payments store (replace with database in production)
payments = {
    "PAY001": {
        "payment_id": "PAY001",
        "order_id": "ORD001",
        "customer_id": "3",
        "amount": 8999.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_status": "completed",
        "transaction_id": "TXN_12345678",
        "payment_date": "2024-01-15T10:45:00Z",
        "card_last_four": "1234",
        "card_brand": "visa",
        "billing_address": {
            "street": "789 Customer Rd",
            "city": "Customer Town",
            "state": "CT",
            "zip_code": "13579",
            "country": "US"
        },
        "notes": "Deposit payment for Tesla Model S",
        "created_at": "2024-01-15T10:45:00Z",
        "updated_at": "2024-01-15T10:45:00Z"
    },
    "PAY002": {
        "payment_id": "PAY002",
        "order_id": "ORD002",
        "customer_id": "3",
        "amount": 4599.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_status": "pending",
        "transaction_id": None,
        "payment_date": "2024-01-20T14:30:00Z",
        "card_last_four": "1234",
        "card_brand": "visa",
        "billing_address": {
            "street": "789 Customer Rd",
            "city": "Customer Town",
            "state": "CT",
            "zip_code": "13579",
            "country": "US"
        },
        "notes": "Deposit payment for Audi A4",
        "created_at": "2024-01-20T14:30:00Z",
        "updated_at": "2024-01-20T14:30:00Z"
    }
}

# Pydantic models
class BillingAddress(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class Payment(BaseModel):
    payment_id: str
    order_id: str
    customer_id: str
    amount: float
    currency: str
    payment_method: str  # credit_card, debit_card, bank_transfer, cash
    payment_status: str  # pending, processing, completed, failed, refunded
    transaction_id: Optional[str]
    payment_date: str
    card_last_four: Optional[str]
    card_brand: Optional[str]
    billing_address: BillingAddress
    notes: Optional[str]
    created_at: str
    updated_at: str

class PaymentCreate(BaseModel):
    order_id: str
    amount: float
    currency: str = "USD"
    payment_method: str
    card_number: str  # This would be tokenized in production
    card_expiry: str
    card_cvv: str
    billing_address: BillingAddress
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    payment_status: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class RefundRequest(BaseModel):
    amount: Optional[float] = None  # If None, refund full amount
    reason: str
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

def generate_payment_id() -> str:
    """Generate unique payment ID"""
    return f"PAY{str(uuid.uuid4())[:8].upper()}"

def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    return f"TXN_{str(uuid.uuid4()).replace('-', '').upper()[:12]}"

def process_payment(payment_data: PaymentCreate) -> dict:
    """Mock payment processing (integrate with real payment gateway)"""
    # In production, this would integrate with Stripe, PayPal, etc.
    # For demo purposes, we'll simulate payment processing
    
    card_number = payment_data.card_number
    if card_number.startswith("4111"):  # Test success card
        return {
            "status": "completed",
            "transaction_id": generate_transaction_id(),
            "card_last_four": card_number[-4:],
            "card_brand": "visa"
        }
    elif card_number.startswith("4000"):  # Test failure card
        return {
            "status": "failed",
            "transaction_id": None,
            "card_last_four": card_number[-4:],
            "card_brand": "visa"
        }
    else:  # Default to pending
        return {
            "status": "processing",
            "transaction_id": generate_transaction_id(),
            "card_last_four": card_number[-4:],
            "card_brand": "unknown"
        }

# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "payments-api", "timestamp": datetime.utcnow()}

@app.get("/payments", response_model=List[Payment])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    token_data: dict = Depends(verify_token)
):
    """List payments with optional filtering"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    filtered_payments = []
    
    for payment in payments.values():
        # Apply role-based filtering
        if user_role == "customer" and payment["customer_id"] != user_id:
            continue
        
        # Apply query filters
        if status and payment["payment_status"] != status:
            continue
        if customer_id and payment["customer_id"] != customer_id:
            continue
        
        filtered_payments.append(payment)
    
    result = filtered_payments[skip:skip + limit]
    payment_list = [Payment(**p) for p in result]
    
    logger.info(f"Listed {len(payment_list)} payments for user {user_id}")
    return payment_list

@app.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(payment_id: str, token_data: dict = Depends(verify_token)):
    """Get payment by ID"""
    if payment_id not in payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payments[payment_id]
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and payment["customer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "dealer", "customer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    logger.info(f"Retrieved payment {payment_id}")
    return Payment(**payment)

@app.post("/payments", response_model=Payment)
async def create_payment(
    payment_data: PaymentCreate,
    token_data: dict = Depends(verify_token)
):
    """Process a new payment"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Only customers can create payments for themselves
    if user_role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create payments"
        )
    
    # Process payment
    payment_result = process_payment(payment_data)
    
    payment_id = generate_payment_id()
    current_time = datetime.utcnow().isoformat() + "Z"
    
    new_payment = {
        "payment_id": payment_id,
        "customer_id": user_id,
        "payment_date": current_time,
        "created_at": current_time,
        "updated_at": current_time,
        "payment_status": payment_result["status"],
        "transaction_id": payment_result["transaction_id"],
        "card_last_four": payment_result["card_last_four"],
        "card_brand": payment_result["card_brand"],
        **payment_data.dict(exclude={"card_number", "card_expiry", "card_cvv"})
    }
    
    payments[payment_id] = new_payment
    logger.info(f"Created new payment {payment_id} with status {payment_result['status']}")
    
    return Payment(**new_payment)

@app.put("/payments/{payment_id}", response_model=Payment)
async def update_payment(
    payment_id: str,
    payment_update: PaymentUpdate,
    token_data: dict = Depends(verify_token)
):
    """Update payment (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if payment_id not in payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payments[payment_id]
    updated_payment = payment.copy()
    update_data = payment_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        updated_payment[field] = value
    
    updated_payment["updated_at"] = datetime.utcnow().isoformat() + "Z"
    payments[payment_id] = updated_payment
    
    logger.info(f"Updated payment {payment_id}")
    return Payment(**updated_payment)

@app.post("/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    refund_request: RefundRequest,
    token_data: dict = Depends(verify_token)
):
    """Process payment refund (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if payment_id not in payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payments[payment_id]
    
    if payment["payment_status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed payments can be refunded"
        )
    
    refund_amount = refund_request.amount or payment["amount"]
    if refund_amount > payment["amount"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed original payment amount"
        )
    
    # In production, process refund with payment gateway
    refund_id = f"REF{str(uuid.uuid4())[:8].upper()}"
    
    # Update payment status
    updated_payment = payment.copy()
    updated_payment["payment_status"] = "refunded"
    updated_payment["updated_at"] = datetime.utcnow().isoformat() + "Z"
    updated_payment["notes"] = f"Refunded ${refund_amount}. Reason: {refund_request.reason}"
    
    payments[payment_id] = updated_payment
    
    logger.info(f"Processed refund {refund_id} for payment {payment_id}")
    return {
        "message": "Refund processed successfully",
        "refund_id": refund_id,
        "refund_amount": refund_amount,
        "original_payment_id": payment_id
    }

@app.get("/payments/order/{order_id}")
async def get_order_payments(
    order_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get payments for a specific order"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    order_payments = []
    for payment in payments.values():
        if payment["order_id"] == order_id:
            # Check permissions
            if user_role == "customer" and payment["customer_id"] != user_id:
                continue
            order_payments.append(payment)
    
    payment_list = [Payment(**p) for p in order_payments]
    
    logger.info(f"Retrieved {len(payment_list)} payments for order {order_id}")
    return {
        "payments": payment_list,
        "total": len(payment_list),
        "order_id": order_id
    }

@app.get("/payments/customer/{customer_id}")
async def get_customer_payments(
    customer_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get payments for a specific customer"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "customer" and user_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "customer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    customer_payments = [p for p in payments.values() if p["customer_id"] == customer_id]
    payment_list = [Payment(**p) for p in customer_payments]
    
    logger.info(f"Retrieved {len(payment_list)} payments for customer {customer_id}")
    return {
        "payments": payment_list,
        "total": len(payment_list),
        "customer_id": customer_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)