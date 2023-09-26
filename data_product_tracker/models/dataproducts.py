import pathlib
import typing
from io import IOBase

import mmh3
from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from data_product_tracker.models import base


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_hierarchies"

    parent_id = Column(BigInteger, ForeignKey("data_products.id"))
    child_id = Column(BigInteger, ForeignKey("data_products.id"))


class DataProduct(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_products"

    invocation_id = Column(
        BigInteger, ForeignKey("invocations.id"), nullable=True
    )
    mmh3_hash = Column(BigInteger)
    _path = Column("path", String(256))

    parents = relationship(
        "DataProduct",
        secondary=DataProductHierarchy.__tablename__,
        primaryjoin="DataProduct.id == DataProductHierarchy.child_id",
        secondaryjoin="DataProduct.id == DataProductHierarchy.parent_id",
        backref="children",
    )

    @classmethod
    def from_file(cls, fd: typing.IO) -> "DataProduct":
        path = fd.name
        fd.seek(0)
        hash_val = mmh3.hash64(fd.read())[0]

        instance = cls(path=path, mmh3_hash=hash_val)
        return instance

    @classmethod
    def from_path(cls, path: pathlib.Path) -> "DataProduct":
        with open(path, "rb") as fin:
            return cls.from_file(fin)

    @hybrid_property
    def path(self) -> pathlib.Path:
        return pathlib.Path(self._path)

    @path.setter
    def path(self, value: typing.Union[str, pathlib.Path]):
        if isinstance(value, pathlib.Path):
            path = value
        elif isinstance(value, IOBase):
            path = pathlib.Path(value.name)
        else:
            path = pathlib.Path(value)

        self._path = str(path.expanduser())

    @path.expression
    def path(cls):
        return cls._path

    def calculate_hash(self, raise_=False):
        try:
            with open(self.path, "rb") as fin:
                hash_val = mmh3.hash64(fin.read())
            self.mmh3_hash = hash_val
        except (FileNotFoundError, OSError):
            self.mmh3_hash = None
            if raise_:
                raise
