from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from app.services.reminder_service import (
    cancel_reminder,
    create_reminder,
    get_reminder,
    get_reminders,
    update_reminder,
)

router = APIRouter()
_oauth2 = OAuth2PasswordBearer(tokenUrl="http://localhost/auth/login")


@router.post("/", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: ReminderCreate,
    user_id: str = Depends(get_current_user_id),
    token: str = Depends(_oauth2),
    db: AsyncSession = Depends(get_db),
):
    return await create_reminder(data, user_id, db, token)


@router.get("/", response_model=list[ReminderRead])
async def list_reminders(
    event_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_reminders(user_id, event_id, db)


@router.get("/{reminder_id}", response_model=ReminderRead)
async def get_one(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_reminder(reminder_id, user_id, db)


@router.put("/{reminder_id}", response_model=ReminderRead)
async def update(
    reminder_id: str,
    data: ReminderUpdate,
    user_id: str = Depends(get_current_user_id),
    token: str = Depends(_oauth2),
    db: AsyncSession = Depends(get_db),
):
    return await update_reminder(reminder_id, data, user_id, db, token)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await cancel_reminder(reminder_id, user_id, db)
