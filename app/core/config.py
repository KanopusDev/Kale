from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os
import secrets
import json
from pathlib import Path

class Settings(BaseSettings):
    """Professional configuration management"""
    
    # ===== APPLICATION SETTINGS =====
    APP_NAME: str = "Kale Email API Platform"
    APP_DESCRIPTION: str = "Professional Email API Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DOMAIN: str = os.getenv("DOMAIN", "kale.kanopus.org")
    API_V1_STR: str = "/api"
    
    # ===== SECURITY SETTINGS =====
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(64))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    API_KEY_EXPIRE_DAYS: int = int(os.getenv("API_KEY_EXPIRE_DAYS", "365"))
    
    # Password Policy
    MIN_PASSWORD_LENGTH: int = 12
    MAX_PASSWORD_LENGTH: int = 128
    REQUIRE_PASSWORD_COMPLEXITY: bool = True
    
    # Session Management
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    MAX_CONCURRENT_SESSIONS: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))
    ACCOUNT_LOCKOUT_ATTEMPTS: int = int(os.getenv("ACCOUNT_LOCKOUT_ATTEMPTS", "5"))
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES", "30"))
    
    # ===== DATABASE SETTINGS =====
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kale.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", "30"))
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    # Database Backup
    AUTO_BACKUP_ENABLED: bool = os.getenv("AUTO_BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    
    # ===== REDIS SETTINGS =====
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "20"))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))
    REDIS_RETRY_ATTEMPTS: int = int(os.getenv("REDIS_RETRY_ATTEMPTS", "3"))
    
    # Cache Settings
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour
    CACHE_USER_DATA_TTL: int = int(os.getenv("CACHE_USER_DATA_TTL", "900"))  # 15 minutes
    CACHE_TEMPLATES_TTL: int = int(os.getenv("CACHE_TEMPLATES_TTL", "1800"))  # 30 minutes
    
    # ===== EMAIL RATE LIMITS =====
    UNVERIFIED_DAILY_LIMIT: int = int(os.getenv("UNVERIFIED_DAILY_LIMIT", "1000"))
    VERIFIED_DAILY_LIMIT: int = int(os.getenv("VERIFIED_DAILY_LIMIT", "-1"))  # -1 = unlimited
    ENTERPRISE_DAILY_LIMIT: int = int(os.getenv("ENTERPRISE_DAILY_LIMIT", "-1"))
    
    # API Rate Limiting
    API_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
    API_RATE_LIMIT_PER_HOUR: int = int(os.getenv("API_RATE_LIMIT_PER_HOUR", "3600"))
    API_RATE_LIMIT_PER_DAY: int = int(os.getenv("API_RATE_LIMIT_PER_DAY", "50000"))
    
    # Burst Limits
    EMAIL_BURST_LIMIT: int = int(os.getenv("EMAIL_BURST_LIMIT", "100"))
    EMAIL_BURST_WINDOW_MINUTES: int = int(os.getenv("EMAIL_BURST_WINDOW_MINUTES", "5"))
    
    # ===== ADMIN SETTINGS =====
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    SUPER_ADMIN_EMAIL: str = os.getenv("SUPER_ADMIN_EMAIL")
    
    # ===== CORS AND SECURITY =====
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    ALLOWED_METHODS: str = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,PATCH,OPTIONS")
    ALLOWED_HEADERS: str = os.getenv("ALLOWED_HEADERS", "*")
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    CONTENT_SECURITY_POLICY_ENABLED: bool = os.getenv("CONTENT_SECURITY_POLICY_ENABLED", "true").lower() == "true"
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year
    
    # ===== LOGGING SETTINGS =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/kale.log")
    LOG_ROTATION_SIZE: str = os.getenv("LOG_ROTATION_SIZE", "10MB")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    
    # Structured Logging
    ENABLE_STRUCTURED_LOGGING: bool = os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true"
    LOG_REQUEST_DETAILS: bool = os.getenv("LOG_REQUEST_DETAILS", "true").lower() == "true"
    
    # ===== EMAIL SERVICE SETTINGS =====
    DEFAULT_FROM_EMAIL: str = os.getenv("DEFAULT_FROM_EMAIL", "support@kanopus.org")
    DEFAULT_FROM_NAME: str = os.getenv("DEFAULT_FROM_NAME", "Kale Email API")
    
    # Email Processing
    EMAIL_QUEUE_WORKERS: int = int(os.getenv("EMAIL_QUEUE_WORKERS", "4"))
    EMAIL_RETRY_ATTEMPTS: int = int(os.getenv("EMAIL_RETRY_ATTEMPTS", "3"))
    EMAIL_RETRY_DELAY_SECONDS: int = int(os.getenv("EMAIL_RETRY_DELAY_SECONDS", "30"))
    
    # SMTP Connection Pool
    SMTP_CONNECTION_POOL_SIZE: int = int(os.getenv("SMTP_CONNECTION_POOL_SIZE", "10"))
    SMTP_CONNECTION_TIMEOUT: int = int(os.getenv("SMTP_CONNECTION_TIMEOUT", "30"))
    
    # ===== FILE UPLOAD SETTINGS =====
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES: str = os.getenv("ALLOWED_FILE_TYPES", ".jpg,.jpeg,.png,.pdf,.txt,.csv,.docx,.xlsx")
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # ===== MONITORING AND METRICS =====
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    
    # Health Checks
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    ENABLE_HEALTH_CHECKS: bool = os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"
    
    # ===== BACKGROUND TASKS =====
    TASK_QUEUE_SIZE: int = int(os.getenv("TASK_QUEUE_SIZE", "1000"))
    WORKER_THREADS: int = int(os.getenv("WORKER_THREADS", "4"))
    BACKGROUND_TASK_TIMEOUT: int = int(os.getenv("BACKGROUND_TASK_TIMEOUT", "300"))
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # ===== PWA SETTINGS =====
    PWA_NAME: str = "Kale Email API"
    PWA_SHORT_NAME: str = "Kale"
    PWA_THEME_COLOR: str = "#667eea"
    PWA_BACKGROUND_COLOR: str = "#ffffff"
    
    # ===== TEMPLATE SETTINGS =====
    TEMPLATE_CACHE_SIZE: int = int(os.getenv("TEMPLATE_CACHE_SIZE", "1000"))
    TEMPLATE_VALIDATION_ENABLED: bool = os.getenv("TEMPLATE_VALIDATION_ENABLED", "true").lower() == "true"
    MAX_TEMPLATE_SIZE_KB: int = int(os.getenv("MAX_TEMPLATE_SIZE_KB", "500"))
    
    # ===== API DOCUMENTATION =====
    ENABLE_DOCS: bool = not (ENVIRONMENT == "production" and not DEBUG)
    DOCS_URL: Optional[str] = "/docs" if ENABLE_DOCS else None
    REDOC_URL: Optional[str] = "/redoc" if ENABLE_DOCS else None
    
    # ===== EXTERNAL INTEGRATIONS =====
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    ENABLE_SENTRY: bool = SENTRY_DSN is not None
    
    # Webhook Settings
    WEBHOOK_TIMEOUT: int = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
    WEBHOOK_RETRY_ATTEMPTS: int = int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3"))
    
    # ===== COMPUTED PROPERTIES =====
    @property
    def admin_emails_list(self) -> List[str]:
        """Get list of admin emails"""
        return [email.strip() for email in self.ADMIN_EMAILS.split(",") if email.strip()]
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get list of allowed origins"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_methods_list(self) -> List[str]:
        """Get list of allowed methods"""
        return [method.strip() for method in self.ALLOWED_METHODS.split(",") if method.strip()]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get list of allowed file types"""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",") if ext.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.ENVIRONMENT.lower() == "testing"
    
    @property
    def api_base_url(self) -> str:
        """Get API base URL"""
        protocol = "https" if self.is_production else "http"
        return f"{protocol}://{self.DOMAIN}"
    
    @property
    def database_url_formatted(self) -> str:
        """Get properly formatted database URL"""
        if self.DATABASE_URL.startswith("sqlite"):
            # Ensure absolute path for SQLite
            if ":///" in self.DATABASE_URL:
                db_path = self.DATABASE_URL.split("///")[1]
                if not os.path.isabs(db_path):
                    db_path = os.path.abspath(db_path)
                return f"sqlite:///{db_path}"
        return self.DATABASE_URL
    
    @property
    def log_config(self) -> dict:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "structured": {
                    "()": "structlog.stdlib.ProcessorFormatter",
                    "processor": "structlog.dev.ConsoleRenderer" if self.is_development else "structlog.processors.JSONRenderer",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "structured" if self.ENABLE_STRUCTURED_LOGGING else "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "formatter": "structured" if self.ENABLE_STRUCTURED_LOGGING else "default",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.LOG_FILE_PATH,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
            },
            "loggers": {
                "": {
                    "level": self.LOG_LEVEL,
                    "handlers": ["default", "file"],
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
                "sqlalchemy": {
                    "level": "WARNING",
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }
    
    def validate_settings(self) -> None:
        """Validate configuration settings"""
        errors = []
        
        # Production-specific validations
        if self.is_production:
            if self.SECRET_KEY == "your-secret-key-here" or len(self.SECRET_KEY) < 32:
                errors.append("Production requires a strong SECRET_KEY (min 32 characters)")
            
            if self.DEBUG:
                errors.append("DEBUG must be False in production")
            
            if self.DATABASE_URL.startswith("sqlite") and "memory" in self.DATABASE_URL:
                errors.append("Production cannot use in-memory database")
        
        # Email limits validation
        if self.UNVERIFIED_DAILY_LIMIT < 0:
            errors.append("UNVERIFIED_DAILY_LIMIT must be non-negative")
        
        if self.EMAIL_BURST_LIMIT <= 0:
            errors.append("EMAIL_BURST_LIMIT must be positive")
        
        # Rate limiting validation
        if self.API_RATE_LIMIT_PER_MINUTE <= 0:
            errors.append("API_RATE_LIMIT_PER_MINUTE must be positive")
        
        # Admin validation
        if not self.admin_emails_list:
            errors.append("At least one admin email must be configured")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

# Create global settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
except ValueError as e:
    if settings.is_production:
        raise e
    else:
        print(f"Configuration warnings: {e}")

# Create necessary directories
os.makedirs("logs", exist_ok=True)
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs("backups", exist_ok=True)
