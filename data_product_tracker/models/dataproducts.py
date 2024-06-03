import pathlib
import typing
from io import FileIO

import mmh3
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_product_tracker.models import base


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_hierarchies"

    parent_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("data_products.id")
    )
    child_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("data_products.id")
    )


class DataProduct(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_products"

    invocation_id: Mapped[typing.Optional[int]] = mapped_column(
        sa.BigInteger, sa.ForeignKey("invocations.id")
    )
    mmh3_hash: Mapped[typing.Optional[int]] = mapped_column(sa.BigInteger)
    _path: Mapped[pathlib.Path] = mapped_column("path", sa.String(length=256))

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

    def calculate_hash(self):
        raise NotImplementedError

    @hybrid_property
    def path(self):
        return pathlib.Path(self._path)

    @path.inplace.setter
    def _path_setter(self, value: typing.Union[pathlib.Path, FileIO, str]):
        if isinstance(value, pathlib.Path):
            self._path = value.resolve()
        elif isinstance(value, str):
            self._path = pathlib.Path(value).resolve()
        elif isinstance(value, FileIO):
            self._path = pathlib.Path(value.name).resolve()
        else:
            try:
                self._path = pathlib.Path(getattr(value, "name")).resolve()
            except AttributeError:
                raise ValueError(f"Cannot cast {value} to path-like")

    @path.inplace.expression
    @classmethod
    def _path_expr(cls):
        return cls._path
