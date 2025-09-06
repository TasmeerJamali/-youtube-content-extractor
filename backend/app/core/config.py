"""
Configuration management for YouTube Content Extractor.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = "YouTube Content Extractor"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    secret_key: str = Field(..., env="SECRET_KEY")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # YouTube API Configuration
    youtube_api_key: str = Field(..., env="YOUTUBE_API_KEY")
    youtube_api_service_name: str = Field(default="youtube", env="YOUTUBE_API_SERVICE_NAME")
    youtube_api_version: str = Field(default="v3", env="YOUTUBE_API_VERSION")
    youtube_api_quota_limit: int = Field(default=10000, env="YOUTUBE_API_QUOTA_LIMIT")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    test_database_url: Optional[str] = Field(None, env="TEST_DATABASE_URL")
    connection_pool_size: int = Field(default=20, env="CONNECTION_POOL_SIZE")
    max_overflow: int = Field(default=30, env="MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Caching Configuration
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    
    # Rate Limiting Configuration
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    
    # NLP Configuration
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    sentence_transformer_model: str = Field(
        default="all-MiniLM-L6-v2", env="SENTENCE_TRANSFORMER_MODEL"
    )
    
    # Security Configuration
    cors_origins: List[str] = Field(
        default=["*"],  # Allow all origins for development
        env="CORS_ORIGINS"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Performance Configuration
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Feature Flags
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse list environment variables
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",")]
        
        if isinstance(self.allowed_hosts, str):
            self.allowed_hosts = [host.strip() for host in self.allowed_hosts.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


# Database URL for different environments
def get_database_url() -> str:
    """Get the appropriate database URL based on environment."""
    if settings.environment == "test" and settings.test_database_url:
        return settings.test_database_url
    return settings.database_url