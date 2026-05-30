import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import PyJWTError

from app.core.config import settings
import hashlib

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


class TokenService:
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

    @staticmethod
    def hash_token(token: str) -> str:
        """SHA-256 hash of a token for safe DB storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_token(
        user_id: int,
        email: str,
        token_type: str = "access",
        expiration_minutes: int | None = None,
    ) -> Tuple[str, datetime]:
        issued_at = datetime.now(timezone.utc)

        if expiration_minutes is None:
            expiration_minutes = (
                TokenService.ACCESS_TOKEN_EXPIRE_MINUTES
                if token_type == "access"
                else TokenService.REFRESH_TOKEN_EXPIRE_MINUTES
            )

        expiration = issued_at + timedelta(minutes=expiration_minutes)

        payload = {
            "exp": expiration,
            "iat": issued_at,
            "sub": str(user_id),
            "user_id": user_id,
            "email": email,
            "token_type": token_type,
        }

        encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
        return encoded_jwt, expiration

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except PyJWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication error")
