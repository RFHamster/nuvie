import jwt

from app.core.config import settings
from datetime import datetime, timedelta
from fastapi import Response
from passlib.context import CryptContext
from typing import Any


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


ALGORITHM = 'HS256'


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {'exp': expire, 'sub': str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key='access_token',
        value=f'Bearer {token}',
        httponly=True,
        secure=False,
        samesite='None',
        max_age=7200,  # In seconds
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
