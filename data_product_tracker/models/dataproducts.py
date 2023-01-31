import pathlib
import typing

import mmh3
from sqlalchemy import BigInteger, Column, ForeignKey, String

from data_product_tracker.models import base


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_hierarchies"

    parent_id = Column(BigInteger, ForeignKey("data_products.id"))
    child_id = Column(BigInteger, ForeignKey("data_products.id"))


class DataProduct(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_products"

    invocation_id = Column(BigInteger, ForeignKey("invocations.id"))
    mmh3_hash = Column(BigInteger)
    path = Column(String(256))

    @classmethod
    def from_file(cls, fd: typing.IO) -> "DataProduct":
        path = fd.name
        fd.seek(0)
        hash_val = mmh3.hash64(fd.read())

        instance = cls(path=path, mmh3_hash=hash_val)
        return instance

    @classmethod
    def from_path(cls, path: pathlib.Path) -> "DataProduct":
        with open(path, "rb") as fin:
            return cls.from_file(fin)
