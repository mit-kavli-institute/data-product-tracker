"""Data product and hierarchy models."""

import pathlib
import typing
from io import FileIO

import mmh3
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_product_tracker.models import base
from data_product_tracker.models.base import PathType


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    """Represents parent-child relationships between data products."""

    __tablename__ = "data_product_hierarchies"

    parent_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("data_products.id")
    )
    child_id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.ForeignKey("data_products.id")
    )


class DataProduct(base.Base, base.CreatedOnMixin):
    """Represents a tracked data product with metadata and relationships."""

    __tablename__ = "data_products"

    invocation_id: Mapped[typing.Optional[int]] = mapped_column(
        sa.BigInteger, sa.ForeignKey("invocations.id")
    )
    mmh3_hash: Mapped[typing.Optional[int]] = mapped_column(sa.BigInteger)
    _path: Mapped[pathlib.Path] = mapped_column("path", PathType(length=256))

    parents = relationship(
        "DataProduct",
        secondary=DataProductHierarchy.__tablename__,
        primaryjoin="DataProduct.id == DataProductHierarchy.child_id",
        secondaryjoin="DataProduct.id == DataProductHierarchy.parent_id",
        backref="children",
    )

    def __repr__(self):
        """Return string representation of DataProduct."""
        return f"<DP {self.id} {self.path}>"

    @classmethod
    def from_file(cls, fd: typing.IO) -> "DataProduct":
        """Create DataProduct from file object.

        Parameters
        ----------
        fd : typing.IO
            File object to create DataProduct from.

        Returns
        -------
        DataProduct
            New DataProduct instance with calculated hash.
        """
        path = fd.name
        fd.seek(0)
        hash_val = mmh3.hash64(fd.read())[0]

        instance = cls(path=path, mmh3_hash=hash_val)
        return instance

    @classmethod
    def from_path(cls, path: pathlib.Path) -> "DataProduct":
        """Create DataProduct from file path.

        Parameters
        ----------
        path : pathlib.Path
            Path to file to create DataProduct from.

        Returns
        -------
        DataProduct
            New DataProduct instance, with hash if file exists.
        """
        if path.exists():
            with open(path, "rb") as fin:
                return cls.from_file(fin)
        else:
            # File doesn't exist yet, create without hash
            return cls(path=path)

    def calculate_hash(self):
        """Calculate hash for this data product.

        Raises
        ------
        NotImplementedError
            Hash calculation not yet implemented.
        """
        raise NotImplementedError

    @hybrid_property
    def path(self):
        """Get the path of this data product."""
        return self._path

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
                self._path = pathlib.Path(value.name).resolve()
            except AttributeError:
                raise ValueError(f"Cannot cast {value} to path-like")

    @path.inplace.expression
    @classmethod
    def _path_expr(cls):
        # Handle comparison with Path objects in SQL expressions
        return sa.type_coerce(cls._path, PathType)
