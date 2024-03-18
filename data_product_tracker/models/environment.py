import functools
import os
from importlib.metadata import distributions
from socket import gethostname

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from data_product_tracker.models import base


class Environment(base.Base, base.CreatedOnMixin):
    __tablename__ = "environments"

    host = Column(String(64), default=gethostname, nullable=False)
    variables = relationship(
        "Variable",
        back_populates="environments",
        secondary="variable_environment_mappings",
    )
    libraries = relationship(
        "Library",
        back_populates="environments",
        secondary="library_environment_mappings",
    )


class VariableEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "variable_environment_mappings"

    environment_id = Column(
        BigInteger, ForeignKey(Environment.id), nullable=False
    )
    variable_id = Column(
        BigInteger, ForeignKey("variables.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("environment_id", "variable_id"),
        Index("idx_variable_id", "variable_id"),
    )

    def __repr__(self):
        return (
            "VariableEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"variable_id={self.variable_id})"
        )


class LibraryEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "library_environment_mappings"

    environment_id = Column(
        BigInteger, ForeignKey(Environment.id), nullable=False
    )
    library_id = Column(BigInteger, ForeignKey("libraries.id"), nullable=False)
    __table_args__ = (UniqueConstraint("environment_id", "library_id"),)

    def __repr__(self):
        return (
            "LibraryEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"library_id={self.library_id})"
        )


class Variable(base.Base, base.CreatedOnMixin):
    __tablename__ = "variables"

    key = Column(String(64), nullable=False)
    value = Column(Text(), nullable=False)
    environments = relationship(
        "Environment",
        back_populates="variables",
        secondary="variable_environment_mappings",
    )

    __table_args__ = (UniqueConstraint("key", "value"),)

    def __hash__(self):
        return hash(self.key, self.value)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return other.key == self.key and other.value == self.value

    @classmethod
    def get_os_variables(cls, db):
        q = cls.select()
        variables = []
        filters = []
        for key, value in os.environ.items():
            filters.append(sa.and_(cls.key == key, cls.value == value))
        q = q.where(functools.reduce(sa.or_, filters))
        with db:
            hits = {v: v for v in db.execute(q).scalar()}
            if len(hits) == len(os.environ):
                # Short circuiti
                return list(hits.values())

            for row in os.environ.items():
                if row not in hits:
                    variable = cls(
                        key=key,
                        value=value,
                    )
                    db.add(variable)
                else:
                    variable = hits[row]

                variables.append(variable)
            db.commit()

        return variables


class Library(base.Base, base.CreatedOnMixin):
    __tablename__ = "libraries"

    name = Column(String(64), nullable=False)
    version = Column(String(64), nullable=False)
    environments = relationship(
        "Environment",
        back_populates="libraries",
        secondary="library_environment_mappings",
    )

    __table_args__ = (UniqueConstraint("name", "version"),)

    def __hash__(self):
        return hash(self.name, self.version)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name and self.version == other.version

    @classmethod
    def get_installed_python_libraries(cls, db):
        q = cls.select()
        libraries = []
        filters = []
        for distribution in distributions():
            filters.append(
                sa.and_(
                    cls.name == distribution.metadata["Name"],
                    cls.version == distribution.version,
                )
            )
        q = q.where(functools.reduce(sa.or_, filters))
        with db:
            hits = {lib: lib for lib in db.execute(q).scalars()}
            if len(hits) == len(list(distributions())):
                # Short circuit and return all found libraries
                return list(hits.values())

            for distribution in distributions():
                key = (distribution.metadata["Name"], distribution.version)
                if key not in hits:
                    library = cls(
                        name=distribution.metadata["Name"],
                        version=distribution.version,
                    )
                    db.add(library)
                else:
                    library = hits[key]

                libraries.append(library)
            db.commit()

        return libraries
