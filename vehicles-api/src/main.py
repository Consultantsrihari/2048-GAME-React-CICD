from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api:8000")

app = FastAPI(
    title="Vehicles API",
    description="Vehicle data management microservice",
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

# In-memory vehicles store (replace with database in production)
vehicles = {
    "VIN001": {
        "vin": "VIN001",
        "make": "Tesla",
        "model": "Model S",
        "year": 2023,
        "color": "Red",
        "engine_type": "Electric",
        "transmission": "Automatic",
        "fuel_type": "Electric",
        "mileage": 15000,
        "price": 89999.99,
        "status": "available",
        "features": ["Autopilot", "Premium Audio", "Glass Roof"],
        "location": "Los Angeles, CA",
        "dealer_id": "2",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "VIN002": {
        "vin": "VIN002",
        "make": "BMW",
        "model": "X5",
        "year": 2023,
        "color": "Blue",
        "engine_type": "Gasoline",
        "transmission": "Automatic",
        "fuel_type": "Gasoline",
        "mileage": 8500,
        "price": 65999.99,
        "status": "sold",
        "features": ["Navigation", "Leather Seats", "Sunroof"],
        "location": "New York, NY",
        "dealer_id": "2",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z"
    },
    "VIN003": {
        "vin": "VIN003",
        "make": "Audi",
        "model": "A4",
        "year": 2022,
        "color": "White",
        "engine_type": "Gasoline",
        "transmission": "Manual",
        "fuel_type": "Gasoline",
        "mileage": 25000,
        "price": 45999.99,
        "status": "reserved",
        "features": ["Navigation", "Heated Seats"],
        "location": "Chicago, IL",
        "dealer_id": "2",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-10T00:00:00Z"
    }
}

# Pydantic models
class Vehicle(BaseModel):
    vin: str
    make: str
    model: str
    year: int
    color: str
    engine_type: str
    transmission: str
    fuel_type: str
    mileage: int
    price: float
    status: str  # available, sold, reserved, maintenance
    features: List[str]
    location: str
    dealer_id: str
    created_at: str
    updated_at: str

class VehicleCreate(BaseModel):
    vin: str
    make: str
    model: str
    year: int
    color: str
    engine_type: str
    transmission: str
    fuel_type: str
    mileage: int
    price: float
    features: List[str] = []
    location: str
    dealer_id: str

class VehicleUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    engine_type: Optional[str] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    price: Optional[float] = None
    status: Optional[str] = None
    features: Optional[List[str]] = None
    location: Optional[str] = None
    dealer_id: Optional[str] = None

class VehicleSearch(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    status: Optional[str] = None
    location: Optional[str] = None

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

# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vehicles-api", "timestamp": datetime.utcnow()}

@app.get("/vehicles", response_model=List[Vehicle])
async def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    make: Optional[str] = None,
    token_data: dict = Depends(verify_token)
):
    """List vehicles with optional filtering"""
    filtered_vehicles = []
    
    for vehicle in vehicles.values():
        if status and vehicle["status"] != status:
            continue
        if make and vehicle["make"].lower() != make.lower():
            continue
        filtered_vehicles.append(vehicle)
    
    result = filtered_vehicles[skip:skip + limit]
    vehicle_list = [Vehicle(**v) for v in result]
    
    logger.info(f"Listed {len(vehicle_list)} vehicles")
    return vehicle_list

@app.get("/vehicles/{vin}", response_model=Vehicle)
async def get_vehicle(vin: str, token_data: dict = Depends(verify_token)):
    """Get vehicle by VIN"""
    if vin not in vehicles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    vehicle = vehicles[vin]
    logger.info(f"Retrieved vehicle {vin}")
    return Vehicle(**vehicle)

@app.post("/vehicles", response_model=Vehicle)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    token_data: dict = Depends(verify_token)
):
    """Create a new vehicle (admin or dealer only)"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    if user_role not in ["admin", "dealer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or dealer access required"
        )
    
    # For dealers, ensure they can only create vehicles for themselves
    if user_role == "dealer" and vehicle_data.dealer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealers can only create vehicles for themselves"
        )
    
    if vehicle_data.vin in vehicles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this VIN already exists"
        )
    
    current_time = datetime.utcnow().isoformat() + "Z"
    new_vehicle = {
        **vehicle_data.dict(),
        "status": "available",
        "created_at": current_time,
        "updated_at": current_time
    }
    
    vehicles[vehicle_data.vin] = new_vehicle
    logger.info(f"Created new vehicle {vehicle_data.vin}")
    
    return Vehicle(**new_vehicle)

@app.put("/vehicles/{vin}", response_model=Vehicle)
async def update_vehicle(
    vin: str,
    vehicle_update: VehicleUpdate,
    token_data: dict = Depends(verify_token)
):
    """Update vehicle (admin or owning dealer only)"""
    if vin not in vehicles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    vehicle = vehicles[vin]
    
    # Check permissions
    if user_role == "dealer" and vehicle["dealer_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "dealer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or dealer access required"
        )
    
    updated_vehicle = vehicle.copy()
    update_data = vehicle_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        updated_vehicle[field] = value
    
    updated_vehicle["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vehicles[vin] = updated_vehicle
    
    logger.info(f"Updated vehicle {vin}")
    return Vehicle(**updated_vehicle)

@app.delete("/vehicles/{vin}")
async def delete_vehicle(vin: str, token_data: dict = Depends(verify_token)):
    """Delete vehicle (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if vin not in vehicles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    del vehicles[vin]
    logger.info(f"Deleted vehicle {vin}")
    
    return {"message": f"Vehicle {vin} deleted successfully"}

@app.post("/vehicles/search")
async def search_vehicles(
    search_params: VehicleSearch,
    skip: int = 0,
    limit: int = 100,
    token_data: dict = Depends(verify_token)
):
    """Advanced vehicle search"""
    filtered_vehicles = []
    
    for vehicle in vehicles.values():
        # Apply filters
        if search_params.make and vehicle["make"].lower() != search_params.make.lower():
            continue
        if search_params.model and vehicle["model"].lower() != search_params.model.lower():
            continue
        if search_params.year_min and vehicle["year"] < search_params.year_min:
            continue
        if search_params.year_max and vehicle["year"] > search_params.year_max:
            continue
        if search_params.price_min and vehicle["price"] < search_params.price_min:
            continue
        if search_params.price_max and vehicle["price"] > search_params.price_max:
            continue
        if search_params.status and vehicle["status"] != search_params.status:
            continue
        if search_params.location and search_params.location.lower() not in vehicle["location"].lower():
            continue
        
        filtered_vehicles.append(vehicle)
    
    result = filtered_vehicles[skip:skip + limit]
    vehicle_list = [Vehicle(**v) for v in result]
    
    logger.info(f"Search returned {len(vehicle_list)} vehicles")
    return {
        "vehicles": vehicle_list,
        "total": len(filtered_vehicles),
        "search_params": search_params.dict(exclude_unset=True)
    }

@app.get("/vehicles/dealer/{dealer_id}")
async def get_dealer_vehicles(
    dealer_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get vehicles for a specific dealer"""
    user_role = token_data.get("role")
    user_id = token_data.get("user_id")
    
    # Check permissions
    if user_role == "dealer" and user_id != dealer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "dealer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or dealer access required"
        )
    
    dealer_vehicles = [v for v in vehicles.values() if v["dealer_id"] == dealer_id]
    vehicle_list = [Vehicle(**v) for v in dealer_vehicles]
    
    logger.info(f"Retrieved {len(vehicle_list)} vehicles for dealer {dealer_id}")
    return {
        "vehicles": vehicle_list,
        "total": len(vehicle_list),
        "dealer_id": dealer_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)