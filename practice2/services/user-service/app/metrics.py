from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

USERS_REGISTERED_TOTAL = Counter(
    "users_registered_total",
    "Total number of registered users",
)
USERS_LOGGED_IN_TOTAL = Counter(
    "users_logged_in_total",
    "Total number of successful logins",
)
USERS_ACTIVE_TOTAL = Counter(
    "users_active_total",
    "Total number of unique active sessions (login events)",
)

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
)
