from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_token, is_token_blacklisted
from app.services.user_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_redis_pool: Redis | None = None


def set_redis(redis: Redis) -> None:
    global _redis_pool
    _redis_pool = redis


async def get_redis() -> Redis:
    return _redis_pool


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if await is_token_blacklisted(token, redis):
            raise credentials_exception
        token_data = decode_token(token)
    except ValueError:
        raise credentials_exception

    user = await get_user_by_id(token_data.user_id, db)
    if user is None or not user.is_active:
        raise credentials_exception
    return user
