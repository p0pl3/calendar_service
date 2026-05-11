from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

EVENTS_CREATED_TOTAL = Counter(
    "events_created_total",
    "Total number of calendar events created",
)
REMINDERS_CREATED_TOTAL = Counter(
    "reminders_created_total",
    "Total number of reminders created",
)
REMINDERS_PUBLISHED_TOTAL = Counter(
    "reminders_published_total",
    "Total number of reminder messages published to RabbitMQ",
)

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
)
