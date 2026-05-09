from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.messaging import close_rabbitmq, connect_rabbitmq
from app.routers.events import router as events_router
from app.routers.reminders import router as reminders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_rabbitmq()
    yield
    await close_rabbitmq()
    await engine.dispose()


app = FastAPI(
    title="Event Service",
    version="1.0.0",
    description="Manages calendar events and reminders",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(reminders_router, prefix="/reminders", tags=["reminders"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "event-service"}
