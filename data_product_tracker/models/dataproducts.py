from sqlalchemy import BigInteger, Column, ForeignKey, String

from data_product_tracker.models import base


class DataProductHierarchy(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_product_hierarchies"

    parent_id = Column(BigInteger, ForeignKey("data_products.id"))
    child_id = Column(BigInteger, ForeignKey("data_products.id"))


class DataProduct(base.Base, base.CreatedOnMixin):
    __tablename__ = "data_products"

    invocation_id = Column(BigInteger, ForeignKey("invocations.id"))
    path = Column(String(256))
