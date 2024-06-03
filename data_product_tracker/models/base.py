from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)

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
