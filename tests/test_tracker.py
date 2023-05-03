import pathlib
from tempfile import TemporaryDirectory

import sqlalchemy as sa

from data_product_tracker.models.dataproducts import DataProduct


def test_trackers(database, tracker):
    select_dp = sa.select(DataProduct)
    with TemporaryDirectory() as _dir:
        test_path = pathlib.Path(_dir)

        def some_function(filename_base):
            with open(test_path / f"{filename_base}_1.txt", "wt") as fout:
                tracker.track(fout)

            with open(test_path / f"{filename_base}_2.txt", "wt") as fout2:
                tracker.track(fout2, parents=[fout])

        some_function("test_file")
        ref_path = test_path / "test_file_2.txt"
        with database as db:
            dp = db.execute(
                select_dp.where(DataProduct.path == ref_path)
            ).scalar()
            assert dp.parents[0].path == test_path / "test_file_1.txt"


def test_tracker_resolution(database, tracker):
    select_dp = sa.select(DataProduct)
    with TemporaryDirectory() as _dir:
        test_path = pathlib.Path(_dir)

        def some_function(filename_base):
            with open(test_path / f"{filename_base}_1.txt", "wt") as fout:
                tracker.track(fout)

            with open(test_path / f"{filename_base}_2.txt", "wt") as fout2:
                tracker.track(fout2, parents=[fout])

        def another_dep(parent):
            with open(test_path / "child_dataproduct.txt", "wt") as fout:
                tracker.track(fout, parents=[parent])

        some_function("test_file")
        parent_path = test_path / "test_file_1.txt"

        another_dep(parent_path)

        ref_path = test_path / "child_dataproduct.txt"

        with database as db:
            dp = db.execute(
                select_dp.where(DataProduct.path == ref_path)
            ).scalar()
            assert dp.parents[0].path == parent_path


def test_variable_hints(database, tracker):
    select_dp = sa.select(DataProduct)
    with TemporaryDirectory() as _dir:
        test_path = pathlib.Path(_dir)

        variables = [1, 2, 3]
        other_variables = "some other type"
        fout = open(test_path / "test.out", "wb")
        fout.write(b"BYTES")
        tracker.track(fout)
        tracker.associate_variables(fout, variables, other_variables)

        dependent = open(test_path / "dep.out", "wt")
        dependent.write("Ooga booga")
        tracker.track(dependent, variable_hints=[variables])

        with database as db:
            dep_path = test_path / "dep.out"
            parent_path = test_path / "test.out"
            dp = db.execute(
                select_dp.where(DataProduct.path == dep_path)
            ).scalar()
            assert dp.parents[0].path == parent_path
