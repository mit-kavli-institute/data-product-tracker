"""Console script for data_product_tracker."""
import sys

import click
import sqlalchemy as sa
from tabulate import tabulate

from data_product_tracker import db
from data_product_tracker.models.dataproducts import DataProduct


def _model_to_dict(inst: DataProduct, columns: list[str]):
    return {getattr(inst, c) for c in columns}


def _print_query(
    products: list[DataProduct], columns: list[str], table_format: str
):
    data = [_model_to_dict(p, columns) for p in products]

    click.echo(tabulate(data, tablefmt=table_format))


@click.group()
def dpt(args=None):
    """The Main DPT Program"""
    return 0


@dpt.group()
def search():
    """Search"""
    return 0


@search.command()
@click.option("--case/--nocase", default=False)
@click.option("--table-format", "-f", default="simple")
@click.argument("substr")
def subtring(case, table_format, substr):

    if case:
        clause = DataProduct.path.like(f"%{substr}%")
    else:
        clause = DataProduct.path.ilike(f"%{substr}%")

    with db:
        q = sa.select(DataProduct)
        q = q.where(clause)

        _print_query(
            db.execute(q).fetchall(), ["id", "path", "hash_str"], table_format
        )


if __name__ == "__main__":
    sys.exit(dpt())  # pragma: no cover
