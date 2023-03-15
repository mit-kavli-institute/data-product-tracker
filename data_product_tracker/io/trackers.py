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
        self._db = database

    def resolve_environment(self):
        if self.env_id is None:
            env_id, _ = get_or_create_env(self._db)
            self.env_id = env_id

        return self.env_id

    def resolve_dataproduct(self, parent_path):
        if isinstance(parent_path, pathlib.Path):
            path = str(parent_path)
        elif isinstance(parent_path, IOBase):
            path = parent_path.name
        else:
            path = parent_path

        try:
            return self._product_map[path]
        except KeyError:
            with self._db as db:
                q = sa.select(DataProduct).where(
                    DataProduct.path == parent_path
                )
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
