from celery import Celery

from app.config import settings

celery_app = Celery(
    "scheduler",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.check_reminders"],
)

celery_app.conf.update(
    beat_schedule={
        "check-due-reminders-every-minute": {
            "task": "app.tasks.check_reminders.check_and_publish_due_reminders",
            "schedule": 60.0,
        }
    },
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_max_tasks_per_child=100,
)
