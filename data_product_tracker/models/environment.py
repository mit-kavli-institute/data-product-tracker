import functools
import os
from socket import gethostname

import pkg_resources
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_product_tracker.models import base


class Environment(base.Base, base.CreatedOnMixin):
    __tablename__ = "environments"

    host: Mapped[str] = mapped_column(sa.String(64), default=gethostname)
    variables: Mapped[list["Variable"]] = relationship(
        "Variable",
        back_populates="environments",
        secondary="variable_environment_mappings",
    )
    libraries: Mapped[list["Library"]] = relationship(
        "Library",
        back_populates="environments",
        secondary="library_environment_mappings",
    )


class VariableEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "variable_environment_mappings"

    environment_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey(Environment.id)
    )
    variable_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("variables.id")
    )

    __table_args__ = (sa.UniqueConstraint("environment_id", "variable_id"),)

    def __repr__(self):
        return (
            "VariableEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"variable_id={self.variable_id})"
        )


class LibraryEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "library_environment_mappings"

    environment_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey(Environment.id)
    )
    library_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("libraries.id")
    )
    __table_args__ = (sa.UniqueConstraint("environment_id", "library_id"),)

    def __repr__(self):
        return (
            "LibraryEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"library_id={self.library_id})"
        )


class Variable(base.Base, base.CreatedOnMixin):
    __tablename__ = "variables"

    key: Mapped[str] = mapped_column(sa.String(64))
    value: Mapped[str]
    environments = relationship(
        "Environment",
        back_populates="variables",
        secondary="variable_environment_mappings",
    )

    __table_args__ = (sa.UniqueConstraint("key", "value"),)

    def __hash__(self):
        return hash((self.key, self.value))

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
                    key, value = row
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

    name: Mapped[str] = mapped_column(sa.String(64))
    version: Mapped[str] = mapped_column(sa.String(64))
    environments: Mapped[list["Environment"]] = relationship(
        "Environment",
        back_populates="libraries",
        secondary="library_environment_mappings",
    )

    __table_args__ = (sa.UniqueConstraint("name", "version"),)

    def __hash__(self):
        return hash((self.name, self.version))

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
