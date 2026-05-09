from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import hash_password
from uuid import uuid4


async def create_user(data: UserCreate, session: AsyncSession) -> User:
    repo = UserRepository(session)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        id=str(uuid4()),
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    return await repo.create(user)


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    repo = UserRepository(session)
    return await repo.get_by_email(email)


async def get_user_by_id(user_id: str, session: AsyncSession) -> User | None:
    repo = UserRepository(session)
    return await repo.get_by_id(user_id)


async def update_user(user: User, data: UserUpdate, session: AsyncSession) -> User:
    repo = UserRepository(session)
    if data.username is not None:
        user.username = data.username
    user.updated_at = datetime.now(timezone.utc)
    return await repo.update(user)


async def soft_delete_user(user: User, session: AsyncSession) -> None:
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
