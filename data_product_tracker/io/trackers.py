import inspect
import pathlib
from io import IOBase

import sqlalchemy as sa

from data_product_tracker.conn import db
from data_product_tracker.models.dataproducts import (
    DataProduct,
    DataProductHierarchy,
)
from data_product_tracker.models.invocation import Invocation
from data_product_tracker.reflection import get_or_create_env


class DataProductTracker:
    def __init__(self):
        self.assign_db(db)
        self._product_map = {}
        self._invocation_cache = {}
        self.env_id = None

    def assign_db(self, database):
        """
        Reassign the database object for the tracker. Useful for testing.
        """
        self._db = database

    def resolve_environment(self):
        """
        Get or create the current environment id.
        """
        if self.env_id is None:
            env_id, _ = get_or_create_env(self._db)
            self.env_id = env_id

        return self.env_id

    def resolve_dataproduct(self, path):
        """
        Attempt to resolve the given path to an existing dataproduct.
        """
        if isinstance(path, pathlib.Path):
            path = str(path)
        elif isinstance(path, IOBase):
            path = path.name
        else:
            path = path

        try:
            return self._product_map[path]
        except KeyError:
            with self._db as db:
                q = sa.select(DataProduct).where(DataProduct.path == path)
                result = db.execute(q).scalar()

                if result is None:
                    raise

                self._product_map[str(result.path)] = result
            return result

    def resolve_invocation(self, invocation_stack):
        reference_frame = invocation_stack[0]
        key = ".".join((s.function for s in invocation_stack))

        function = reference_frame.function
        env_id = self.resolve_environment()
        if key in self._invocation_cache:
            invocation_id = self._invocation_cache[key]
        else:
            with self._db as db:
                invocation = Invocation.reflect_call(
                    function, environment_id=env_id
                )
                db.add(invocation)
                db.commit()
                self._invocation_cache[key] = invocation.id
                invocation_id = invocation.id
        return invocation_id

    def track(
        self,
        target_file,
        parents=None,
        hash_override=None,
        determine_hash=False,
    ):
        """
        Track the given file/path and establish relations to any provided
        parents. This call will result in SQL emissions.

        TODO:
        Determine if ASYNC calls will make this more performant in high IO
        environments.

        Parameters
        ----------
        target_file: Union[str, os.PathLike, io.IOBase]
            The file to track. If given an IOBase object, it must implement
            some form of `instance.name` to provide a location on disk.
        parents: Optional[list[Union[str, os.PathLike, io.IOBase]]]
            Any parents that were needed in creating the `target_file`.
        hash_override: Optional[int]
            If given override any hash value assigned to the data product.
        determine_hash: Optional[bool]
            If true, determine the hash value of the `target_file` using the
            non-cryptographic murmur3 hash algorithm.
        """
        invocation_id = self.resolve_invocation(inspect.stack()[1:])
        with self._db as db:
            dp = DataProduct(path=target_file, invocation_id=invocation_id)
            if hash_override is not None:
                dp.mmh3 = hash_override
            elif determine_hash is True:
                dp.calculate_hash()

            db.add(dp)
            db.commit()  # Emit SQL and return assigned id
            child_id = dp.id

            # Determine relationships
            relationships = []
            parents = [] if parents is None else parents
            for parent in parents:
                parent_id = self.resolve_dataproduct(parent).id
                rel = {
                    "parent_id": parent_id,
                    "child_id": child_id,
                }
                relationships.append(rel)
            db.bulk_insert_mappings(DataProductHierarchy, relationships)
            db.commit()
            self._product_map[str(dp.path)] = dp

            return dp


tracker = DataProductTracker()
