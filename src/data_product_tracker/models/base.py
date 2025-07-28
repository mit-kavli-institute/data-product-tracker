"""Base models for Data Product Tracker.

This module provides the base SQLAlchemy declarative models that all other
models inherit from, including common fields and functionality.
"""

import pathlib
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):
    """Base model class for all Data Product Tracker models.

    This class provides common functionality for all database models,
    including an auto-incrementing primary key ID field and utility methods.

    Attributes
    ----------
    id : Mapped[int]
        Primary key identifier. Uses Integer for SQLite and BigInteger for PostgreSQL.
    type_annotation_map : dict
        Maps Python types to SQLAlchemy column types for automatic type conversion.

    Methods
    -------
    select(*attrs)
        Create a SQLAlchemy select statement for this model.

    Notes
    -----
    The ID field uses Integer with a PostgreSQL variant to ensure compatibility
    with both SQLite (for testing) and PostgreSQL (for production).
    """

    id: Mapped[int] = mapped_column(
        sa.Integer().with_variant(sa.BigInteger(), "postgresql"),
        primary_key=True,
    )

    # Type Hint Registration
    type_annotation_map = {pathlib.Path: sa.String}

    @classmethod
    def select(cls, *attrs: str):
        """Create a SQLAlchemy select statement for this model.

        Parameters
        ----------
        *attrs : str
            Optional attribute names to select. If not provided, selects the entire model.

        Returns
        -------
        sqlalchemy.sql.Select
            A SQLAlchemy select statement that can be executed.

        Examples
        --------
        >>> # Select entire model
        >>> query = MyModel.select()
        >>>
        >>> # Select specific attributes
        >>> query = MyModel.select('id', 'name')
        """
        if len(attrs) > 0:
            return sa.select(*[getattr(cls, attr) for attr in attrs])

        return sa.select(cls)


class CreatedOnMixin:
    """Mixin class that adds a created_on timestamp to models.

    This mixin provides automatic timestamp tracking for when records are created.
    It also creates a BRIN index on the created_on column for efficient time-based
    queries in PostgreSQL.

    Attributes
    ----------
    created_on : Mapped[datetime]
        Timestamp when the record was created. Automatically set to current time.

    Notes
    -----
    The BRIN (Block Range Index) is used for PostgreSQL to efficiently index
    time-series data. This index type is ignored for SQLite databases.
    """

    created_on: Mapped[datetime] = mapped_column(default=sa.func.now())

    @declared_attr.directive
    def __table_args__(cls):
        """Generate table arguments including indexes.

        Returns
        -------
        tuple
            Table arguments including a BRIN index on created_on for PostgreSQL.
        """
        tablename = getattr(cls, "__tablename__")
        return (
            sa.Index(
                f"idx_{tablename}_created_on",
                "created_on",
                postgresql_using="brin",
            ),
        )
