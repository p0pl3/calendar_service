import asyncio
import json
import logging
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.metrics import NOTIFICATIONS_FAILED_TOTAL, NOTIFICATIONS_SENT_TOTAL, instrumentator
from app.notifiers.email_notifier import send_email
from app.schemas.notification import ReminderMessage

logger = logging.getLogger(__name__)

QUEUE_NAME = "reminder_tasks"
_consumer_task: asyncio.Task | None = None


async def handle_message(body: bytes) -> None:
    try:
        data = ReminderMessage.model_validate_json(body)
    except Exception as exc:
        logger.error("Failed to parse message: %s — body: %s", exc, body[:200])
        return

    logger.info("Handling reminder_id=%s channels=%s", data.reminder_id, data.channels)

    tasks = []
    if "email" in data.channels:
        tasks.append(("email", send_email(data)))

    if tasks:
        results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)
        for (channel, _), r in zip(tasks, results):
            if isinstance(r, Exception):
                logger.error("Notification delivery error: %s", r)
                NOTIFICATIONS_FAILED_TOTAL.labels(channel=channel).inc()
            else:
                NOTIFICATIONS_SENT_TOTAL.labels(channel=channel).inc()


async def start_amqp_consumer() -> None:
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)
                queue = await channel.declare_queue(QUEUE_NAME, durable=True)
                logger.info("AMQP consumer started on queue '%s'", QUEUE_NAME)
                async for message in queue:
                    async with message.process(ignore_processed=True):
                        await handle_message(message.body)
        except asyncio.CancelledError:
            logger.info("AMQP consumer cancelled")
            return
        except Exception as exc:
            logger.error("AMQP consumer error: %s — reconnecting in 5s", exc)
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    _consumer_task = asyncio.create_task(start_amqp_consumer())
    instrumentator.expose(app, include_in_schema=False)
    yield
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    description="Delivers reminders via email",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator.instrument(app)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "notification-service"}
