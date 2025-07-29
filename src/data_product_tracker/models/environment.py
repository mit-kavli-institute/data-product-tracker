"""Environment, library, and variable models."""

import functools
import os
from importlib.metadata import distributions
from socket import gethostname

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_product_tracker.libraries import Distribution
from data_product_tracker.models import base
from data_product_tracker.variables import OSVariable


class Environment(base.Base, base.CreatedOnMixin):
    """Represents a computational environment with variables and libraries."""

    __tablename__ = "environments"

    host: Mapped[str] = mapped_column(sa.String(), default=gethostname)
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

    __table_args__ = (sa.Index("idx_environment_host", "host"),)


class VariableEnvironmentMap(base.Base, base.CreatedOnMixin):
    """Maps variables to environments."""

    __tablename__ = "variable_environment_mappings"

    environment_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey(Environment.id)
    )
    variable_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("variables.id")
    )

    __table_args__ = (
        sa.UniqueConstraint("environment_id", "variable_id"),
        sa.Index("idx_variable_id", "variable_id"),
    )

    def __repr__(self):
        """Return string representation."""
        return (
            "VariableEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"variable_id={self.variable_id})"
        )

    @classmethod
    def matching_env_id_q(cls, os_variables: list[OSVariable]):
        """Query for environment IDs matching given variables.

        Parameters
        ----------
        os_variables : list[OSVariable]
            List of OS variables to match.

        Returns
        -------
        sqlalchemy.sql.Select
            Query for matching environment IDs.
        """
        q = (
            sa.select(cls.environment_id)
            .join(Variable, Variable.id == cls.variable_id)
            .where(Variable.filter_by_variables(os_variables))
            .group_by(cls.environment_id)
            .having(sa.func.count(cls.variable_id) == len(os_variables))
        )
        return q


class LibraryEnvironmentMap(base.Base, base.CreatedOnMixin):
    """Maps libraries to environments."""

    __tablename__ = "library_environment_mappings"

    environment_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey(Environment.id)
    )
    library_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("libraries.id")
    )
    __table_args__ = (sa.UniqueConstraint("environment_id", "library_id"),)

    def __repr__(self):
        """Return string representation."""
        return (
            "LibraryEnvironmentMap("
            f"environment_id={self.environment_id}, "
            f"library_id={self.library_id})"
        )

    @classmethod
    def matching_env_id_q(cls, distributions: list[Distribution]):
        """Query for environment IDs matching given distributions.

        Parameters
        ----------
        distributions : list[Distribution]
            List of distributions to match.

        Returns
        -------
        sqlalchemy.sql.Select
            Query for matching environment IDs.
        """
        q = (
            sa.select(cls.environment_id)
            .join(Library, Library.id == cls.library_id)
            .where(Library.filter_by_distributions(distributions))
            .group_by(cls.environment_id)
            .having(sa.func.count(cls.library_id) == len(distributions))
        )
        return q


class Variable(base.Base, base.CreatedOnMixin):
    """Represents an environment variable."""

    __tablename__ = "variables"

    key: Mapped[str]
    value: Mapped[str]
    environments = relationship(
        "Environment",
        back_populates="variables",
        secondary="variable_environment_mappings",
    )

    __table_args__ = (
        sa.UniqueConstraint("key", "value"),
        sa.Index("idx_variable_key_value", "key", "value"),
    )

    def __hash__(self):
        """Return hash of variable key-value pair."""
        return hash((self.key, self.value))

    def __eq__(self, other):
        """Check equality based on key and value."""
        if not isinstance(other, self.__class__):
            return False
        return other.key == self.key and other.value == self.value

    def __repr__(self):
        """Return string representation."""
        return f"<OSVar '{self.key}' => '{self.value}'>"

    @classmethod
    def compare_to_variable(
        cls, os_variable: OSVariable
    ) -> sa.ColumnElement[bool]:
        """Create SQL comparison for OSVariable.

        Parameters
        ----------
        os_variable : OSVariable
            Variable to compare against.

        Returns
        -------
        sa.ColumnElement[bool]
            SQL expression for comparison.
        """
        return sa.and_(
            cls.key == os_variable.key, cls.value == os_variable.value
        )

    @classmethod
    def filter_by_variables(
        cls, os_variables: list[OSVariable]
    ) -> sa.ColumnElement[bool]:
        """Create filter for multiple OS variables.

        Parameters
        ----------
        os_variables : list[OSVariable]
            Variables to filter by.

        Returns
        -------
        sa.ColumnElement[bool]
            SQL OR expression for all variables.
        """
        clauses = [cls.compare_to_variable(var) for var in os_variables]
        # Handle empty list case to avoid deprecation warning
        if not clauses:
            return sa.false()
        return sa.or_(*clauses)

    @classmethod
    def get_os_variables(cls, db):
        """Get or create Variable instances for current OS environment.

        Parameters
        ----------
        db : Session
            Database session.

        Returns
        -------
        list[Variable]
            List of Variable instances from environment.
        """
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
    """Represents an installed Python library/package."""

    __tablename__ = "libraries"

    name: Mapped[str]
    version: Mapped[str]
    environments: Mapped[list["Environment"]] = relationship(
        "Environment",
        back_populates="libraries",
        secondary="library_environment_mappings",
    )

    __table_args__ = (
        sa.UniqueConstraint("name", "version"),
        sa.Index("idx_library_name_version", "name", "version"),
    )

    def __hash__(self):
        """Return hash of library name-version pair."""
        return hash((self.name, self.version))

    def __eq__(self, other):
        """Check equality based on name and version."""
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name and self.version == other.version

    def __repr__(self):
        """Return string representation."""
        return f"<Library {self.name} '{self.version}'"

    @classmethod
    def compare_to_distribution(
        cls, distribution: Distribution
    ) -> sa.ColumnElement[bool]:
        """Create SQL comparison for Distribution.

        Parameters
        ----------
        distribution : Distribution
            Distribution to compare against.

        Returns
        -------
        sa.ColumnElement[bool]
            SQL expression for comparison.
        """
        return sa.and_(
            cls.name == distribution.name,
            cls.version == distribution.version,
        )

    @classmethod
    def filter_by_distributions(
        cls, distributions: list[Distribution]
    ) -> sa.ColumnElement[bool]:
        """Create filter for multiple distributions.

        Parameters
        ----------
        distributions : list[Distribution]
            Distributions to filter by.

        Returns
        -------
        sa.ColumnElement[bool]
            SQL OR expression for all distributions.
        """
        clauses = [
            cls.compare_to_distribution(distribution)
            for distribution in distributions
        ]
        # Handle empty list case to avoid deprecation warning
        if not clauses:
            return sa.false()
        return sa.or_(*clauses)

    @classmethod
    def get_installed_python_libraries(cls, db):
        """Get or create Library instances for installed packages.

        Parameters
        ----------
        db : Session
            Database session.

        Returns
        -------
        list[Library]
            List of Library instances from environment.
        """
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
                key = (
                    distribution.metadata["Name"],
                    distribution.version,
                )
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
