from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from app.core.config import settings
import secrets
import string
import logging
import hashlib
import hmac
import base64
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

logger = logging.getLogger(__name__)

# Enhanced password context with multiple schemes
pwd_context = CryptContext(
    schemes=["bcrypt"],  # Use only bcrypt to avoid scrypt issues
    deprecated="auto",
    bcrypt__rounds=12  # Higher rounds for production
)

class SecurityManager:
    """Professional security manager"""
    
    def __init__(self):
        # Initialize encryption key for sensitive data
        self._init_encryption_key()
        
    def _init_encryption_key(self):
        """Initialize encryption key from secret key"""
        # Derive encryption key from SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'kale_encryption_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        self.cipher_suite = Fernet(key)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password with Professional security"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a cryptographically secure API key"""
        # Use multiple entropy sources
        entropy1 = secrets.token_urlsafe(32)
        entropy2 = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:16]
        entropy3 = secrets.token_hex(16)
        
        combined = f"{entropy1}{entropy2}{entropy3}"
        api_key = f"kale_{hashlib.sha256(combined.encode()).hexdigest()[:32]}"
        
        return api_key
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Create a secure hash of the API key for storage"""
        return hashlib.sha256(f"{api_key}{settings.SECRET_KEY}".encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash"""
        try:
            return hmac.compare_digest(
                SecurityManager.hash_api_key(plain_key),
                hashed_key
            )
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with enhanced security"""
        try:
            to_encode = data.copy()
            
            # Add security claims
            now = datetime.utcnow()
            if expires_delta:
                expire = now + expires_delta
            else:
                expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({
                "exp": expire,
                "iat": now,
                "jti": secrets.token_urlsafe(16)  # JWT ID for token tracking
            })
            
            # Add audience and issuer claims for production only
            if not settings.DEBUG and settings.ENVIRONMENT == "production":
                to_encode.update({
                    "nbf": now,
                    "iss": settings.DOMAIN,
                    "aud": settings.DOMAIN
                })
            
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM,
                headers={"typ": "JWT", "alg": settings.ALGORITHM}
            )
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token with comprehensive validation"""
        try:
            # For development, use more lenient verification
            if settings.DEBUG or settings.ENVIRONMENT == "development":
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": False,
                        "verify_iat": True,
                        "verify_aud": False,
                        "verify_iss": False,
                        "require_exp": True,
                        "require_iat": True,
                        "require_nbf": False
                    }
                )
            else:
                # Production verification with all claims
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM],
                    audience=settings.DOMAIN,
                    issuer=settings.DOMAIN,
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_iat": True,
                        "verify_aud": True,
                        "verify_iss": True,
                        "require_exp": True,
                        "require_iat": True,
                        "require_nbf": True
                    }
                )
            
            # Additional validation
            if "sub" not in payload:
                logger.error("Token missing subject claim")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create a refresh token for long-term authentication"""
        data = {
            "sub": str(user_id),
            "type": "refresh",
            "scope": "refresh_token"
        }
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return SecurityManager.create_access_token(data, expires_delta)
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, str]:
        """Enhanced password strength validation"""
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"
        
        if len(password) > 128:
            return False, "Password must not exceed 128 characters"
        
        # Check character complexity
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        
        special_chars = r"[!@#$%^&*()_+\-=\[\]{}|;':\".,<>?/~`]"
        if not re.search(special_chars, password):
            return False, "Password must contain at least one special character"
        
        # Check for sequential characters
        if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", password.lower()):
            return False, "Password must not contain sequential characters"
        
        # Check for common weak passwords
        weak_patterns = [
            "password", "123456", "qwerty", "admin", "root", "user",
            "welcome", "login", "pass", "test", "guest", "demo"
        ]
        
        for pattern in weak_patterns:
            if pattern in password.lower():
                return False, f"Password must not contain common words like '{pattern}'"
        
        return True, "Password is strong"
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like SMTP passwords"""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a numeric verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format with comprehensive regex"""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email))
    
    @staticmethod
    def validate_username_format(username: str) -> tuple[bool, str]:
        """Validate username format"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must not exceed 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        
        if username.startswith('-') or username.endswith('-'):
            return False, "Username cannot start or end with a hyphen"
        
        if username.startswith('_') or username.endswith('_'):
            return False, "Username cannot start or end with an underscore"
        
        # Check for reserved usernames
        reserved = [
            'admin', 'root', 'api', 'www', 'mail', 'ftp', 'localhost',
            'system', 'service', 'daemon', 'bin', 'sys', 'user', 'guest',
            'test', 'demo', 'public', 'private', 'secret', 'hidden'
        ]
        
        if username.lower() in reserved:
            return False, f"Username '{username}' is reserved and cannot be used"
        
        return True, "Username is valid"
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent XSS and other attacks"""
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove or escape dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Remove control characters except common whitespace
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        return text.strip()
    
    @staticmethod
    def rate_limit_key(identifier: str, action: str) -> str:
        """Generate consistent rate limit keys"""
        return f"rate_limit:{action}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
        """Check if redirect URL is safe"""
        if not url:
            return False
        
        # Parse URL and check domain
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            
            # Allow relative URLs
            if not parsed.netloc:
                return url.startswith('/') and not url.startswith('//')
            
            # Check against allowed hosts
            return parsed.netloc in allowed_hosts
            
        except Exception:
            return False

# Global security manager instance
security = SecurityManager()
