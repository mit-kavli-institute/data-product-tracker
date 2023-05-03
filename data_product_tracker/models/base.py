from sqlalchemy import BigInteger, Column, DateTime, Index, func
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import declarative_mixin, declared_attr


@as_declarative()
class Base:
    id = Column(BigInteger, primary_key=True)


@declarative_mixin
class CreatedOnMixin:
    created_on = Column(DateTime, default=func.now())

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"idx_{cls.__tablename__}_created_on",
                "created_on",
                postgresql_using="brin",
            ),
        )
