from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from data_product_tracker.models import base


class DataProductTypeHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_type_hierarchies"
    parent_id = Column(BigInteger, ForeignKey("data_product_types.id"))
    child_id = Column(BigInteger, ForeignKey("data_product_types.id"))
    description = Column(Text)


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_hierarchies"
    parent_id = Column(BigInteger, ForeignKey("data_products.id"))
    child_id = Column(BigInteger, ForeignKey("data_products.id"))

    invocation_id = Column(BigInteger, ForeignKey("invocations.id"))


class DataProductType(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_types"

    name = Column(String(64), unique=True)
    description = Column(Text)

    requires = relationship(
        "DataProductType",
        secondary=DataProductTypeHierarchy,
        primaryjoin=DataProductTypeHierarchy.child_id == id,
        secondaryjoin=DataProductTypeHierarchy.parent_id == id,
    )


class DataProduct(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_products"

    path = Column(String(256), unique=True)
    type = Column(BigInteger, ForeignKey(DataProductType.id))
