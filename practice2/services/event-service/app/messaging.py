import json
import logging
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message

from app.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.Channel | None = None
QUEUE_NAME = "reminder_tasks"


async def connect_rabbitmq() -> None:
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()
    await _channel.declare_queue(QUEUE_NAME, durable=True)
    logger.info("Connected to RabbitMQ")


async def close_rabbitmq() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("RabbitMQ connection closed")


async def publish_reminder_message(payload: dict[str, Any]) -> None:
    if _channel is None:
        logger.error("RabbitMQ channel not initialized")
        return
    body = json.dumps(payload, default=str).encode()
    await _channel.default_exchange.publish(
        Message(body=body, delivery_mode=DeliveryMode.PERSISTENT),
        routing_key=QUEUE_NAME,
    )
    logger.info("Published reminder message for reminder_id=%s", payload.get("reminder_id"))
