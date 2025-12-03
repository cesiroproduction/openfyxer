"""Database-compatible custom types for cross-dialect support."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.types import Integer, String, TypeDecorator


class StringArray(TypeDecorator):
    """Store string arrays as JSON on SQLite, ARRAY on PostgreSQL."""

    impl = ARRAY(String)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(ARRAY(String))

    def process_bind_param(self, value, dialect):
        return value


class IntegerArray(TypeDecorator):
    """Store integer arrays as JSON on SQLite, ARRAY on PostgreSQL."""

    impl = ARRAY(Integer)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(ARRAY(Integer))

    def process_bind_param(self, value, dialect):
        return value


class JSONBType(TypeDecorator):
    """Provide JSONB on PostgreSQL and JSON on SQLite."""

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSONB())

    def process_bind_param(self, value, dialect):
        return value
