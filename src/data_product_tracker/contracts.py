"""Contracts for integration tests using the `deal` library."""

import sqlalchemy as sa

from data_product_tracker.models.dataproducts import DataProduct
from data_product_tracker.models.environment import Environment
from data_product_tracker.models.invocation import Invocation


def _pk_in_database(db, Model, pk):
    with db:
        q = sa.select(Model).where(Model.id == pk).exists()
        return db.execute(sa.select(q)).scalar()


def invocation_exists(_):
    """Check if invocation exists in database.

    Parameters
    ----------
    _ : deal.PostContractCase
        Contract case with self and result attributes.

    Returns
    -------
    bool
        True if invocation with given ID exists.
    """
    db = _.self._db
    return _pk_in_database(db, Invocation, _.result)


def environment_exists(_):
    """Check if environment exists in database.

    Parameters
    ----------
    _ : deal.PostContractCase
        Contract case with self and result attributes.

    Returns
    -------
    bool
        True if environment with given ID exists.
    """
    db = _.self._db
    return _pk_in_database(db, Environment, _.result)


def dataproduct_exists(_):
    """Check if data product exists in database.

    Parameters
    ----------
    _ : deal.PostContractCase
        Contract case with self and result attributes.

    Returns
    -------
    bool
        True if data product with given ID exists.
    """
    return _pk_in_database(_.self._db, DataProduct, _.result)


def empty_caches(_):
    """Verify all tracker caches are empty.

    Parameters
    ----------
    _ : deal.PostContractCase
        Contract case with self attribute.

    Returns
    -------
    bool
        True if all caches are empty.
    """
    return (
        len(_.self._product_map) == 0
        and len(_.self._invocation_cache) == 0
        and len(_.self._variable_cache) == 0
    )


def variables_associated_with_file(_):
    """Verify variables are associated with target file.

    Parameters
    ----------
    _ : deal.PostContractCase
        Contract case with self, target_file, and variables.

    Returns
    -------
    bool
        True if all variables map to target file.
    """
    return all(
        _.self._variable_cache[id(var)]
        == _.self.resolve_dataproduct(_.target_file)
        for var in _.variables
    )
