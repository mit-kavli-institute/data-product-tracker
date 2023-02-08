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
