from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
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
    title="Users API",
    description="User profiles management microservice",
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

# In-memory user profiles store (replace with database in production)
user_profiles = {
    "1": {
        "id": "1",
        "email": "admin@autocompany.com",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "+1-555-0101",
        "address": "123 Admin St, Admin City, AC 12345",
        "date_of_birth": "1980-01-01",
        "license_number": "ADM123456789",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "2": {
        "id": "2",
        "email": "dealer@autocompany.com",
        "first_name": "John",
        "last_name": "Dealer",
        "phone": "+1-555-0102",
        "address": "456 Dealer Ave, Dealer City, DC 67890",
        "date_of_birth": "1975-05-15",
        "license_number": "DLR987654321",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "3": {
        "id": "3",
        "email": "customer@autocompany.com",
        "first_name": "Jane",
        "last_name": "Customer",
        "phone": "+1-555-0103",
        "address": "789 Customer Rd, Customer Town, CT 13579",
        "date_of_birth": "1990-12-25",
        "license_number": "CUS456789123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}

# Pydantic models
class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    license_number: Optional[str] = None
    created_at: str
    updated_at: str

class UserProfileCreate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    license_number: Optional[str] = None

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    license_number: Optional[str] = None

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

def get_next_user_id() -> str:
    """Generate next user ID"""
    return str(len(user_profiles) + 1)

# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "users-api", "timestamp": datetime.utcnow()}

@app.get("/users/profile", response_model=UserProfile)
async def get_my_profile(token_data: dict = Depends(verify_token)):
    """Get current user's profile"""
    user_id = token_data.get("user_id")
    if user_id not in user_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    profile = user_profiles[user_id]
    logger.info(f"Retrieved profile for user {user_id}")
    return UserProfile(**profile)

@app.put("/users/profile", response_model=UserProfile)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    token_data: dict = Depends(verify_token)
):
    """Update current user's profile"""
    user_id = token_data.get("user_id")
    if user_id not in user_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    profile = user_profiles[user_id].copy()
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        profile[field] = value
    
    profile["updated_at"] = datetime.utcnow().isoformat() + "Z"
    user_profiles[user_id] = profile
    
    logger.info(f"Updated profile for user {user_id}")
    return UserProfile(**profile)

@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str, token_data: dict = Depends(verify_token)):
    """Get user profile by ID (admin or same user only)"""
    requesting_user_id = token_data.get("user_id")
    user_role = token_data.get("role")
    
    # Check permissions
    if user_role != "admin" and requesting_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if user_id not in user_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    profile = user_profiles[user_id]
    logger.info(f"Retrieved profile for user {user_id} by {requesting_user_id}")
    return UserProfile(**profile)

@app.get("/users", response_model=List[UserProfile])
async def list_user_profiles(
    skip: int = 0,
    limit: int = 100,
    token_data: dict = Depends(verify_token)
):
    """List all user profiles (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    profiles_list = list(user_profiles.values())[skip:skip + limit]
    profiles = [UserProfile(**profile) for profile in profiles_list]
    
    logger.info(f"Listed {len(profiles)} user profiles")
    return profiles

@app.post("/users", response_model=UserProfile)
async def create_user_profile(
    profile_data: UserProfileCreate,
    token_data: dict = Depends(verify_token)
):
    """Create a new user profile (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_id = get_next_user_id()
    current_time = datetime.utcnow().isoformat() + "Z"
    
    new_profile = {
        "id": user_id,
        "email": f"user{user_id}@autocompany.com",  # This should come from auth service
        "created_at": current_time,
        "updated_at": current_time,
        **profile_data.dict()
    }
    
    user_profiles[user_id] = new_profile
    logger.info(f"Created new user profile with ID {user_id}")
    
    return UserProfile(**new_profile)

@app.delete("/users/{user_id}")
async def delete_user_profile(user_id: str, token_data: dict = Depends(verify_token)):
    """Delete user profile (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if user_id not in user_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    del user_profiles[user_id]
    logger.info(f"Deleted user profile {user_id}")
    
    return {"message": f"User profile {user_id} deleted successfully"}

@app.get("/users/search")
async def search_users(
    q: str,
    skip: int = 0,
    limit: int = 100,
    token_data: dict = Depends(verify_token)
):
    """Search users by name or email (admin only)"""
    user_role = token_data.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = q.lower()
    matching_profiles = []
    
    for profile in user_profiles.values():
        if (query in profile["first_name"].lower() or
            query in profile["last_name"].lower() or
            query in profile["email"].lower()):
            matching_profiles.append(profile)
    
    results = matching_profiles[skip:skip + limit]
    profiles = [UserProfile(**profile) for profile in results]
    
    logger.info(f"Search for '{q}' returned {len(profiles)} results")
    return {
        "users": profiles,
        "total": len(matching_profiles),
        "query": q
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)