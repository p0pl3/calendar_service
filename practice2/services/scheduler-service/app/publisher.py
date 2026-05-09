import json
import logging

import pika

from app.config import settings

logger = logging.getLogger(__name__)
QUEUE_NAME = "reminder_tasks"


def publish_reminder_sync(payload: dict) -> None:
    try:
        params = pika.URLParameters(settings.rabbitmq_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(payload, default=str).encode(),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        connection.close()
        logger.info("Published reminder_id=%s", payload.get("reminder_id"))
    except Exception as exc:
        logger.error("Failed to publish reminder: %s", exc)
