import inspect
import pathlib
from itertools import chain

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
        self._variable_cache: dict[int, int] = {}
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
        else:
            try:
                path = path.name
            except AttributeError:
                raise RuntimeError(
                    f"{path} could not be resolved to a resource on disk."
                )

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
        """
        Resolve the invocation using the provided callstack. It is assumed
        that the provided callstack has the appropriate context such that
        the top of the stack is the "invoking" function.

        Visual Example of the Callstack

        [0][ function_call_to_make_file ]  <- desired context
        [1][ function_which_calls ^ ]
        [ ... ]
        [-1][ python entry ]
        """
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

    def resolve_variable_hints(self, *variables):
        """
        Attempt to resolve given variables (objects) to hints provided. If no
        hint was found continue as the variable might have moved in memory
        space.
        """
        ids = []
        for variable in variables:
            try:
                ids.append(self._variable_cache[id(variable)])
            except KeyError:
                continue
        return ids

    def associate_variables(self, target_file, *variables):
        product_id = self.resolve_dataproduct(target_file).id
        for variable in variables:
            self._variable_cache[id(variable)] = product_id

    def track(
        self,
        target_file,
        parents=None,
        variable_hints=None,
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
        target_file: Union[str, os.PathLike, io.FileIO]
            The file to track. If given an FileIO object, it must implement
            some form of `instance.name` to provide a location on disk.
        parents: Optional[list[Union[str, os.PathLike, io.FileIO]]]
            Any parents that were needed in creating the `target_file`.
        variable_hints: Optional[list[Any]]
            Provide variables which will be used to lookup parent relations.
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
            variables = [] if variable_hints is None else variable_hints
            parents = [] if parents is None else parents
            parents = [self.resolve_dataproduct(p).id for p in parents]

            variable_ids = self.resolve_variable_hints(*variables)
            for parent_id in set(chain(variable_ids, parents)):
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
