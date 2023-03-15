import pathlib
from tempfile import TemporaryDirectory

import sqlalchemy as sa


def test_trackers(database, mocker):
    mocker.patch("data_product_tracker.conn.db", new=database)
    from data_product_tracker import tracker
    from data_product_tracker.models.dataproducts import DataProduct

    tracker.assign_db(database)
    tracker.env_id = None

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


def test_tracker_resolution(database, mocker):
    mocker.patch("data_product_tracker.conn.db", new=database)
    from data_product_tracker import tracker
    from data_product_tracker.models.dataproducts import DataProduct

    tracker.assign_db(database)
    tracker.env_id = None

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
