from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

app = FastAPI(
    title="Auth API",
    description="Authentication and authorization microservice",
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

# In-memory user store (replace with database in production)
users_db = {
    "admin@autocompany.com": {
        "id": "1",
        "email": "admin@autocompany.com",
        "hashed_password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "is_active": True
    },
    "dealer@autocompany.com": {
        "id": "2",
        "email": "dealer@autocompany.com",
        "hashed_password": bcrypt.hashpw("dealer123".encode(), bcrypt.gensalt()).decode(),
        "role": "dealer",
        "is_active": True
    },
    "customer@autocompany.com": {
        "id": "3",
        "email": "customer@autocompany.com",
        "hashed_password": bcrypt.hashpw("customer123".encode(), bcrypt.gensalt()).decode(),
        "role": "customer",
        "is_active": True
    }
}

# Pydantic models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "customer"

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Routes
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-api", "timestamp": datetime.utcnow()}

@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user = users_db.get(user_credentials.email)
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "user_id": user["id"]}
    )
    
    logger.info(f"User {user_credentials.email} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600
    }

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = str(len(users_db) + 1)
    hashed_password = get_password_hash(user_data.password)
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "role": user_data.role,
        "is_active": True
    }
    
    users_db[user_data.email] = new_user
    logger.info(f"New user registered: {user_data.email}")
    
    return UserResponse(
        id=user_id,
        email=user_data.email,
        role=user_data.role,
        is_active=True
    )

@app.get("/auth/verify")
async def verify_token_endpoint(token_data: dict = Depends(verify_token)):
    """Verify JWT token and return user info"""
    user = users_db.get(token_data["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"]
    )

@app.get("/auth/users")
async def list_users(token_data: dict = Depends(verify_token)):
    """List all users (admin only)"""
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users_list = []
    for user in users_db.values():
        users_list.append(UserResponse(
            id=user["id"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"]
        ))
    
    return {"users": users_list, "total": len(users_list)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)