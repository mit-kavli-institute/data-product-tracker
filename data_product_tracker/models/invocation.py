import sys
from getpass import getuser

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, ForeignKey, String

from data_product_tracker.models import base


class Invocation(base.Base, base.CreatedOnMixin):
    __tablename__ = "invocations"

    user = Column(String(128), default=getuser)
    function = Column(String(128))
    environment_id = Column(BigInteger, ForeignKey("environments.id"))

    command = Column(sa.Text())

    def __repr__(self):
        return f"<Invocation {self.id}: {self.function}() from {self.command}>"

    @classmethod
    def reflect_call(cls, function, environment_id=None):
        invocation = cls(
            function=function,
            command="".join(sys.argv),
            environment_id=environment_id,
        )
        return invocation
