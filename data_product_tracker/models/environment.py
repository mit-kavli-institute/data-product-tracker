import functools
import os
from socket import gethostname

import pkg_resources
import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from data_product_tracker.models import base


class Environment(base.Base, base.CreatedOnMixin):
    __tablename__ = "environments"

    host = Column(String(64), default=gethostname)
    variables = relationship(
        "VariableEnvironmentMap", back_populates="environment"
    )
    libraries = relationship(
        "LibraryEnvironmentMap", back_populates="environment"
    )


class VariableEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "variable_environment_mappings"

    environment_id = Column(BigInteger, ForeignKey(Environment.id))
    variable_id = Column(BigInteger, ForeignKey("variables.id"))

    environment = relationship("Environment", back_populates="variables")
    variable = relationship("Variable", back_populates="environments")

    __table_args__ = (UniqueConstraint("environment_id", "variable_id"),)


class LibraryEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "library_environment_mappings"

    environment_id = Column(BigInteger, ForeignKey(Environment.id))
    library_id = Column(BigInteger, ForeignKey("libraries.id"))

    environment = relationship("Environment", back_populates="libraries")
    library = relationship("Library", back_populates="environments")

    __table_args__ = (UniqueConstraint("environment_id", "library_id"),)


class Variable(base.Base, base.CreatedOnMixin):
    __tablename__ = "variables"

    key = Column(String(64))
    value = Column(String(256))
    environments = relationship(
        "VariableEnvironmentMap", back_populates="variable"
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

    name = Column(String(64))
    version = Column(String(64))
    environments = relationship(
        "LibraryEnvironmentMap", back_populates="library"
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
        for package in pkg_resources.working_set:
            filters.append(
                sa.and_(
                    cls.name == package.name,
                    cls.version == package.version,
                    cls.location == package.path,
                )
            )
        q = q.where(functools.reduce(sa.or_, filters))
        with db:
            hits = {lib: lib for lib in db.execute(q).scalars()}
            if len(hits) == len(pkg_resources.working_set):
                # Short circuit and return all found libraries
                return list(hits.values())

            for package in pkg_resources.working_set:
                key = (package.name, package.version, package.path)
                if key not in hits:
                    library = cls(
                        name=package.name,
                        version=package.version,
                        location=package.path,
                    )
                    db.add(library)
                else:
                    library = hits[key]

                libraries.append()
            db.commit()

        return libraries
