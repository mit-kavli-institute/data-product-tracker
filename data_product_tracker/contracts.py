"""
This module contains contracts which are used for integration tests.
"""

import sqlalchemy as sa

from data_product_tracker.models.dataproducts import DataProduct
from data_product_tracker.models.environment import Environment
from data_product_tracker.models.invocation import Invocation


def _pk_in_database(db, Model, pk):
    with db:
        q = sa.select(Model).where(Model.id == pk).exists()
        return db.execute(sa.select(q)).scalar()


def invocation_exists(_):
    db = _.self._db
    return _pk_in_database(db, Invocation, _.result)


def environment_exists(_):
    db = _.self._db
    return _pk_in_database(db, Environment, _.result)


def dataproduct_exists(_):
    return _pk_in_database(_.self._db, DataProduct, _.result)
