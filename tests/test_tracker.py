import pathlib
from tempfile import TemporaryDirectory

import sqlalchemy as sa
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from data_product_tracker import tracker as dp_tracker
from data_product_tracker.models.dataproducts import DataProduct

from .conftest import database_obj, ensure_directory
from .strategies import file_paths


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


@settings(deadline=None)
@given(file_paths().filter(lambda p: p != pathlib.Path(".")), st.binary())
def test_tracker_anonymous_file(path, data):
    with database_obj() as db, TemporaryDirectory() as _dir:
        tmpdir = pathlib.Path(_dir)
        full_path = ensure_directory(tmpdir / path)
        with open(full_path, "wb") as fout:
            fout.write(data)
        assert full_path.exists()

        dp_tracker.assign_db(db)
        dp_tracker.env_id = None
        dp_tracker.dump_cache()

        ref_dp = dp_tracker.resolve_dataproduct(full_path)
        assert ref_dp is not None and ref_dp is not None


@settings(deadline=None)
@given(
    file_paths().filter(lambda p: p != pathlib.Path(".")),
    file_paths().filter(lambda p: p != pathlib.Path(".")),
)
def test_anonymous_parent(parent, child):

    # The paths are generated independently of each other, so ensure one path
    # is not made as a directory to another.

    assume(not (parent.is_relative_to(child) or child.is_relative_to(parent)))

    with database_obj() as db, TemporaryDirectory() as _dir:
        tmpdir = pathlib.Path(_dir)
        parent_path = ensure_directory(tmpdir / parent)
        child_path = ensure_directory(tmpdir / child)
        with open(parent_path, "wb") as fout:
            fout.write(b"Foo")
        with open(child_path, "wb") as fout:
            fout.write(b"Bar")

        dp_tracker.assign_db(db)
        dp_tracker.env_id = None
        dp_tracker.dump_cache()

        dp_tracker.track(child_path, parents=[parent_path])


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
