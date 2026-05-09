import json
from sqlalchemy import String, Text, types
from sqlalchemy.dialects.postgresql import ARRAY


class StringListType(types.TypeDecorator):
    """Stores list[str] as ARRAY on PostgreSQL and as JSON text on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String(50)))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name != "postgresql":
            return json.dumps(value) if value is not None else None
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != "postgresql" and isinstance(value, str):
            return json.loads(value)
        return value
