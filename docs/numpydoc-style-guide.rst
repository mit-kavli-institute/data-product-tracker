NumPy Documentation Style Guide
===============================

This project uses NumPy-style docstrings for all modules, classes, and functions.
This guide provides examples and best practices for writing documentation.

Module Docstrings
-----------------

Every module should start with a docstring that describes its purpose::

    """Brief module description.

    Longer description that provides more detail about what the module does,
    its main classes/functions, and how it fits into the larger system.

    Examples
    --------
    >>> from data_product_tracker import tracker
    >>> tracker.track('output.csv', parents=['input.csv'])
    """

Class Docstrings
----------------

Classes should document their purpose, attributes, and methods::

    class DataProduct:
        """Represents a tracked data file or output.

        This class models a data product (file) that is tracked by the system,
        including its metadata and relationships to other data products.

        Parameters
        ----------
        path : pathlib.Path
            Path to the data file.
        hash_value : str, optional
            SHA256 hash of the file contents.

        Attributes
        ----------
        id : int
            Unique identifier in the database.
        path : pathlib.Path
            Absolute path to the file.
        hash_value : str
            SHA256 hash of the file contents.
        created_on : datetime
            Timestamp when the record was created.

        Methods
        -------
        from_path(path)
            Create a DataProduct from a file path.
        compute_hash()
            Calculate the SHA256 hash of the file.

        See Also
        --------
        DataProductHierarchy : Relationships between data products.

        Notes
        -----
        Data products are uniquely identified by their path and hash value.
        The same file with different content will create a new data product.

        Examples
        --------
        >>> dp = DataProduct.from_path('/data/output.csv')
        >>> print(dp.hash_value)
        'a1b2c3d4...'
        """

Function Docstrings
-------------------

Functions should document parameters, returns, and behavior::

    def track(child, parents=None, variable_hints=None):
        """Track a data product and its dependencies.

        Records a data product in the tracking system along with its parent
        dependencies and any variable hints that influenced its creation.

        Parameters
        ----------
        child : str, pathlib.Path, or file-like
            The output file to track.
        parents : list of str, pathlib.Path, or file-like, optional
            Parent files that this output depends on.
        variable_hints : list, optional
            Variables that influenced the creation of this output.

        Returns
        -------
        DataProduct
            The tracked data product object.

        Raises
        ------
        ValueError
            If the child path is invalid or doesn't exist.
        DatabaseError
            If there's an error writing to the database.

        See Also
        --------
        resolve_dataproduct : Lower-level function for resolving paths.

        Notes
        -----
        This function is idempotent - tracking the same file multiple times
        will not create duplicates if the content hasn't changed.

        Examples
        --------
        Track a simple transformation:

        >>> track('output.csv', parents=['input.csv'])

        Track with multiple parents:

        >>> track('merged.csv', parents=['file1.csv', 'file2.csv'])

        Track with variable hints:

        >>> threshold = 0.5
        >>> track('filtered.csv', parents=['data.csv'],
        ...       variable_hints=[threshold])
        """

Best Practices
--------------

1. **Always include a brief one-line summary** at the start
2. **Use proper sections** (Parameters, Returns, Examples, etc.)
3. **Include type information** in parameter descriptions
4. **Provide examples** when the usage might not be obvious
5. **Cross-reference** related classes/functions with See Also
6. **Document exceptions** that the function might raise
7. **Use Notes** for implementation details or warnings

Common Sections
---------------

- **Parameters**: Input parameters
- **Returns**: What the function returns
- **Yields**: For generators
- **Raises**: Exceptions that may be raised
- **See Also**: Related functions/classes
- **Notes**: Additional information
- **References**: Academic references
- **Examples**: Usage examples

Type Annotations
----------------

While NumPy-style docstrings include type information in the parameter
descriptions, this project also uses Python type hints for static analysis::

    def process_data(
        input_file: pathlib.Path,
        threshold: float = 0.5
    ) -> pd.DataFrame:
        """Process data file with threshold filtering.

        Parameters
        ----------
        input_file : pathlib.Path
            Path to input CSV file.
        threshold : float, optional
            Filtering threshold, by default 0.5.

        Returns
        -------
        pd.DataFrame
            Processed data.
        """
