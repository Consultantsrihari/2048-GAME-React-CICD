"""
Configuration settings for Orders API.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Orders API"
    debug: bool = Field(default=False, env="DEBUG")
    version: str = "0.1.0"
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS
    allowed_hosts: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/orders_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # External Services
    auth_service_url: str = Field(
        default="http://auth-api:8000",
        env="AUTH_SERVICE_URL"
    )
    payments_service_url: str = Field(
        default="http://payments-api:8000",
        env="PAYMENTS_SERVICE_URL"
    )
    inventory_service_url: str = Field(
        default="http://inventory-api:8000",
        env="INVENTORY_SERVICE_URL"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    
    # Stripe
    stripe_secret_key: str = Field(
        default="sk_test_...",
        env="STRIPE_SECRET_KEY"
    )
    stripe_webhook_secret: str = Field(
        default="whsec_...",
        env="STRIPE_WEBHOOK_SECRET"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()