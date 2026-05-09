from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from app.config import settings
from app.schemas.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BLACKLIST_PREFIX = "blacklist:"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise ValueError("Invalid token payload")
        return TokenData(user_id=user_id, email=email)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


async def blacklist_token(token: str, redis: Redis) -> None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = payload.get("exp")
        if exp:
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await redis.setex(f"{BLACKLIST_PREFIX}{token}", ttl, "1")
    except JWTError:
        pass


async def is_token_blacklisted(token: str, redis: Redis) -> bool:
    result = await redis.get(f"{BLACKLIST_PREFIX}{token}")
    return result is not None
