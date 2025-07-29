import pathlib
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)
from sqlalchemy.types import TypeDecorator


class PathType(TypeDecorator):
    """Represents a pathlib.Path as a string in the database."""

    impl = sa.String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Path to string when saving to database."""
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert string back to Path when loading from database."""
        if value is not None:
            return pathlib.Path(value)
        return value


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        sa.Integer().with_variant(sa.BigInteger(), "postgresql"),
        primary_key=True,
    )

    # Type Hint Registration
    type_annotation_map = {pathlib.Path: PathType}

    @classmethod
    def select(cls, *attrs: str):
        if len(attrs) > 0:
            return sa.select(*[getattr(cls, attr) for attr in attrs])

        return sa.select(cls)


class CreatedOnMixin:
    created_on: Mapped[datetime] = mapped_column(default=sa.func.now())

    @declared_attr.directive
    def __table_args__(cls):
        tablename = getattr(cls, "__tablename__")
        return (
            sa.Index(
                f"idx_{tablename}_created_on",
                "created_on",
                postgresql_using="brin",
            ),
        )
