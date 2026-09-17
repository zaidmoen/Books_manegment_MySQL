import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from .database import dictionary_cursor, get_db

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_secret_key() -> str:
    """Return the JWT secret and fail clearly when it is not configured."""
    secret_key = os.getenv("SECRET_KEY", "").strip()
    if len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 characters")
    return secret_key


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def find_user_by_username(connection, username: str) -> dict | None:
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT id, username, hashed_password, role
            FROM users
            WHERE username = %s
            """,
            (username,),
        )
        return cursor.fetchone()


def authenticate_user(connection, username: str, password: str) -> dict | None:
    user = find_user_by_username(connection, username)
    if user is None or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(
    *, subject: str, expires_delta: timedelta | None = None
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": subject, "exp": expire},
        get_secret_key(),
        algorithm=ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    connection=Depends(get_db),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = find_user_by_username(connection, username)
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return current_user
