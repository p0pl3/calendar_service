from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.event_service import (
    create_event,
    delete_event,
    get_event,
    get_events,
    update_event,
)

router = APIRouter()


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: EventCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_event(data, user_id, db)


@router.get("/", response_model=list[EventRead])
async def list_events(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_events(user_id, db, from_date, to_date, skip, limit)


@router.get("/{event_id}", response_model=EventRead)
async def get_one(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_event(event_id, user_id, db)


@router.put("/{event_id}", response_model=EventRead)
async def update(
    event_id: str,
    data: EventUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_event(event_id, data, user_id, db)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_event(event_id, user_id, db)
