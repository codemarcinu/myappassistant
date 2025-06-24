"""
JWT Handler for FoodSave AI authentication
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from backend.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """JWT token handler for authentication"""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create access token

        Args:
            data: Data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.info(f"Created access token for user {data.get('sub', 'unknown')}")
        return encoded_jwt

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create refresh token

        Args:
            data: Data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.info(f"Created refresh token for user {data.get('sub', 'unknown')}")
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.PyJWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT token without verification (for debugging)

        Args:
            token: JWT token to decode

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except jwt.PyJWTError as e:
            logger.warning(f"Failed to decode token: {e}")
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash password

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired

        Args:
            token: JWT token

        Returns:
            True if token is expired
        """
        payload = self.decode_token(token)
        if not payload:
            return True

        exp = payload.get("exp")
        if not exp:
            return True

        return datetime.utcnow() > datetime.fromtimestamp(float(exp))


# Global instance
jwt_handler = JWTHandler()
