from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_redis, oauth2_scheme
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.metrics import USERS_ACTIVE_TOTAL, USERS_LOGGED_IN_TOTAL, USERS_REGISTERED_TOTAL
from app.services.auth_service import (
    blacklist_token,
    create_access_token,
    verify_password,
)
from app.services.user_service import create_user, get_user_by_email

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await create_user(data, db)
    USERS_REGISTERED_TOTAL.inc()
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(form_data.username, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    token = create_access_token(user.id, user.email)
    USERS_LOGGED_IN_TOTAL.inc()
    USERS_ACTIVE_TOTAL.inc()
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
    _: User = Depends(get_current_user),
):
    await blacklist_token(token, redis)
