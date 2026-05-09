from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.dependencies import set_redis
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

_redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_client
    _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    set_redis(_redis_client)
    yield
    await _redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="User Service",
    version="1.0.0",
    description="Manages users, authentication and JWT tokens",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "user-service"}
