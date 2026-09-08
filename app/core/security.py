from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

import hashlib
import secrets


password_context=CryptContext(
    schemes=['bcrypt'],
    deprecated="auto",
)



def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(plain_password: str, password_hash: str,) -> bool:
    return password_context.verify(plain_password,password_hash)

def create_access_token(subject: str) -> str:
    expires_at=(datetime.now(timezone.utc) +
                timedelta(minutes=settings.access_token_expire_minutes,))
    payload={
        "sub":subject,
        "exp":expires_at,
    }

    return jwt.encode(payload,settings.jwt_secret_key
                      ,algorithm=settings.jwt_algorithm)

def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(
        refresh_token.encode("utf-8")
    ).hexdigest()