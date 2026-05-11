from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

NOTIFICATIONS_SENT_TOTAL = Counter(
    "notifications_sent_total",
    "Total number of notifications delivered",
    ["channel"],
)
NOTIFICATIONS_FAILED_TOTAL = Counter(
    "notifications_failed_total",
    "Total number of failed notification deliveries",
    ["channel"],
)

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
)
