from socket import gethostname

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

    __table_args__ = UniqueConstraint("environment_id", "variable_id")


class LibraryEnvironmentMap(base.Base, base.CreatedOnMixin):
    __tablename__ = "library_environment_mappings"

    environment_id = Column(BigInteger, ForeignKey(Environment.id))
    library_id = Column(BigInteger, ForeignKey("libraries.id"))

    environment = relationship("Environment", back_populates="libraries")
    library = relationship("Library", back_populates="environments")

    __table_args__ = UniqueConstraint("environment_id", "library_id")


class Variable(base.Base, base.CreatedOnMixin):
    __tablename__ = "variables"

    key = Column(String(64))
    value = Column(String(256))
    environments = relationship(
        "VariableEnvironmentMap", back_populates="variable"
    )

    __table_args__ = UniqueConstraint("key", "value")


class Library(base.Base, base.CreatedOnMixin):
    __tablename__ = "variables"

    name = Column(String(64))
    version = Column(String(64))
    location = Column(String(256))
    environments = relationship(
        "LibraryEnvironmentMap", back_populates="library"
    )

    __table_args__ = UniqueConstraint("name", "version", "location")
