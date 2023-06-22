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


def invocation_exists(args, result):
    db = args.self._db
    return _pk_in_database(db, Invocation, result)


def environment_exists(args, result):
    db = args.self._db
    return _pk_in_database(db, Environment, result)


def dataproduct_exists(args, result):
    return _pk_in_database(args.self._db, DataProduct, result)
