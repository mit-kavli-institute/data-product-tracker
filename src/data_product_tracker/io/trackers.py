"""Data product tracking system for monitoring data dependencies.

This module provides the main interface for tracking data products, their
relationships, and the environments in which they are created.
"""

import inspect
import pathlib
from itertools import chain

import deal
import sqlalchemy as sa

from data_product_tracker import contracts
from data_product_tracker.conn import session_factory
from data_product_tracker.models.dataproducts import (
    DataProduct,
    DataProductHierarchy,
)
from data_product_tracker.models.invocation import Invocation
from data_product_tracker.reflection import get_or_create_env


class DataProductTracker:
    """Main tracker class for data products and their dependencies.

    This class provides methods to track data products (files), their relationships,
    and the environments in which they are created. It maintains internal caches
    for performance and handles automatic environment detection.

    Attributes
    ----------
    env_id : int or None
        ID of the current environment, lazily loaded when needed.
    _db : sqlalchemy.orm.Session
        Database session used for all operations.
    _product_map : dict[str | pathlib.Path, int]
        Cache mapping file paths to data product IDs.
    _invocation_cache : dict
        Cache for function invocation tracking.
    _variable_cache : dict[int, int]
        Cache for variable hint relationships.

    Methods
    -------
    assign_db(database)
        Assign a new database session to the tracker.
    dump_cache()
        Clear all internal caches.
    resolve_environment()
        Get or create the current environment.
    resolve_dataproduct(path)
        Get or create a data product for the given path.
    track(child, parents=None, variable_hints=None)
        Track a data product and its dependencies.
    """

    def __init__(self):
        self.assign_db(session_factory())
        self.env_id = None
        self.dump_cache()

    def assign_db(self, database):
        """Assign a new database session to the tracker.

        This method is primarily used for testing to inject mock sessions.

        Parameters
        ----------
        database : sqlalchemy.orm.Session
            Database session to use for all tracker operations.
        """
        self._db = database

    @deal.ensure(contracts.empty_caches)
    def dump_cache(self):
        """Clear all internal caches.

        Resets all cached mappings to empty dictionaries. This is useful
        when you want to force the tracker to re-query the database.

        Notes
        -----
        This method is decorated with a contract that ensures all caches
        are empty after execution.
        """
        self._product_map: dict[str | pathlib.Path, int] = {}
        self._invocation_cache = {}
        self._variable_cache: dict[int, int] = {}

    @deal.ensure(contracts.environment_exists)
    def resolve_environment(self):
        """Get or create the current environment ID.

        Lazily loads the environment ID based on the current system state,
        including installed libraries and environment variables.

        Returns
        -------
        int
            ID of the current environment.

        Notes
        -----
        The environment is cached after first resolution to avoid repeated
        database queries. The environment includes the hostname, installed
        Python packages, and environment variables.
        """
        if self.env_id is None:
            env_id, _ = get_or_create_env(self._db)
            self.env_id = env_id

        return self.env_id

    @deal.ensure(contracts.dataproduct_exists)
    def resolve_dataproduct(self, path) -> int:
        """Resolve a file path to a data product ID.

        Attempts to find an existing data product for the given path, creating
        one if it doesn't exist.

        Parameters
        ----------
        path : str, pathlib.Path, or file-like object
            Path to the file to track. Can be a string path, Path object,
            or any object with a 'name' attribute (like a file handle).

        Returns
        -------
        int
            ID of the data product in the database.

        Notes
        -----
        Paths are always expanded and resolved to absolute paths before
        storage. The resolved paths are cached to avoid repeated database
        queries.
        """
        if isinstance(path, str):
            path = pathlib.Path(path)

        elif not isinstance(path, pathlib.Path):
            try:
                path = pathlib.Path(path.name)
            except AttributeError:
                # Final catch is resolving by casting to str
                path = str(path)

        # Finally cast everything back to a Path
        path = pathlib.Path(path).expanduser().resolve()

        try:
            return self._product_map[path]
        except KeyError:
            with self._db as db:
                q = sa.select(DataProduct).where(DataProduct.path == path)
                result = db.execute(q).scalar()

                if result is None:
                    result = DataProduct.from_path(path)
                    db.add(result)
                    db.commit()
                self._product_map[result.path] = result.id
            return result.id

    @deal.ensure(contracts.invocation_exists)
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

    @deal.ensure(contracts.variables_associated_with_file)
    def associate_variables(self, target_file, *variables):
        """
        For the given target file, associate the memory pointer locations of
        each passed variable reference.

        Each of these pointer locations can then be used as a hint to resolve
        the passed file later in time.

        Parameters
        ----------
        target_file: Union[str, os.PathLike, io.FileIO]
            The file to be assoicated with the passed variables
        variables: Any
            The variables to associate with the file. The memory addresses
            of the variable will be used. If the memory location changes
            or crosses process memory boundaries this reference will be
            unreliable.

        Notes
        -----
        This method is a quality of life hint. It cannot preserve pointer
        locations across multiprocess boundaries or manual deletion.
        """
        product_id = self.resolve_dataproduct(target_file)
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
            child_path = dp.path

            # Determine relationships
            relationships = []
            variables = [] if variable_hints is None else variable_hints
            parents = [] if parents is None else parents
            parent_ids = [self.resolve_dataproduct(p) for p in parents]

            variable_ids = self.resolve_variable_hints(*variables)
            for parent_id in set(chain(variable_ids, parent_ids)):
                rel = {
                    "parent_id": parent_id,
                    "child_id": child_id,
                }
                relationships.append(rel)
            db.bulk_insert_mappings(DataProductHierarchy, relationships)
            db.commit()
            self._product_map[child_path] = child_id

            return dp


tracker = DataProductTracker()
