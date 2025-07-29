"""Base models and mixins for Data Product Tracker."""

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
    """Represents a pathlib.Path as a string in the database.

    Handles conversion between pathlib.Path objects and database strings.
    """

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
    """Base model class for all Data Product Tracker models.

    Provides common fields and type annotations for all models.
    """

    id: Mapped[int] = mapped_column(
        sa.Integer().with_variant(sa.BigInteger(), "postgresql"),
        primary_key=True,
    )

    # Type Hint Registration
    type_annotation_map = {pathlib.Path: PathType}

    @classmethod
    def select(cls, *attrs: str):
        """Create a SELECT query for this model.

        Parameters
        ----------
        *attrs : str
            Column names to select. If empty, selects entire model.

        Returns
        -------
        sqlalchemy.sql.Select
            Select statement for the model.
        """
        if len(attrs) > 0:
            return sa.select(*[getattr(cls, attr) for attr in attrs])

        return sa.select(cls)


class CreatedOnMixin:
    """Mixin to add created_on timestamp to models."""

    created_on: Mapped[datetime] = mapped_column(default=sa.func.now())

    @declared_attr.directive
    def __table_args__(cls):
        """Generate table arguments for BRIN index on created_on."""
        tablename = cls.__tablename__
        return (
            sa.Index(
                f"idx_{tablename}_created_on",
                "created_on",
                postgresql_using="brin",
            ),
        )
