import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
from .config import config

class SecurityManager:
    """Advanced security management"""
    
    def __init__(self):
        if config.ENCRYPTION_KEY:
            self.fernet = Fernet(config.ENCRYPTION_KEY.encode())
        else:
            self.fernet = None
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self.fernet:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self.fernet:
            return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def generate_token(self, payload: Dict[str, Any], expires_hours: int = 24) -> str:
        """Generate JWT token"""
        payload['exp'] = datetime.utcnow() + timedelta(hours=expires_hours)
        payload['iat'] = datetime.utcnow()
        return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            return jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

# Global security instance
security = SecurityManager()