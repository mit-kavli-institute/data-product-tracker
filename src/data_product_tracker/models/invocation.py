"""Invocation tracking models."""

import sys
from getpass import getuser

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from data_product_tracker.models import base


class Invocation(base.Base, base.CreatedOnMixin):
    """Represents a function invocation context."""

    __tablename__ = "invocations"

    user: Mapped[str] = mapped_column(sa.String(128), default=getuser)
    function: Mapped[str] = mapped_column(sa.String(128))
    environment_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("environments.id")
    )

    command: Mapped[str]

    def __repr__(self):
        """Return string representation."""
        return f"<Invocation {self.id}: {self.function}() from {self.command}>"

    @classmethod
    def reflect_call(cls, function, environment_id=None):
        """Create Invocation from current function context.

        Parameters
        ----------
        function : str
            Name of the function being invoked.
        environment_id : int, optional
            ID of the environment for this invocation.

        Returns
        -------
        Invocation
            New Invocation instance.
        """
        invocation = cls(
            function=function,
            command=" ".join(sys.argv),
            environment_id=environment_id,
        )
        return invocation
