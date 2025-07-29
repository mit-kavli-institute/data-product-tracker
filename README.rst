====================
Data Product Tracker
====================

.. image:: https://img.shields.io/pypi/v/data_product_tracker.svg
        :target: https://pypi.python.org/pypi/data_product_tracker

.. image:: https://github.com/mit-kavli-institute/data-product-tracker/actions/workflows/ci.yml/badge.svg
        :target: https://github.com/mit-kavli-institute/data-product-tracker/actions

.. image:: https://readthedocs.org/projects/data-product-tracker/badge/?version=latest
        :target: https://data-product-tracker.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


A Python library for tracking data products, their dependencies, and execution environments. The Data Product Tracker provides a robust framework for monitoring and managing computational workflows, capturing detailed information about the environment in which data products are generated.

* Free software: MIT license
* Documentation: https://data-product-tracker.readthedocs.io
* Repository: https://github.com/mit-kavli-institute/data-product-tracker


Features
--------

* **Environment Tracking**: Automatically capture and store execution environment details including OS variables, installed libraries, and system configuration
* **Dependency Management**: Track library dependencies with version information for reproducibility
* **Multi-Database Support**: Works with SQLite (default), PostgreSQL, and MySQL databases
* **Performance Optimized**: Bulk operations and caching for efficient tracking at scale
* **Contract-Based Validation**: Uses the ``deal`` library for runtime contract verification
* **Session-Based API**: Clean, context-managed interface for tracking operations
* **Reflection Capabilities**: Query and match existing environments based on current execution context


Installation
------------

Install from PyPI::

    pip install data_product_tracker

For development with all optional dependencies::

    pip install -e ".[dev]"

**Note**: This package depends on ``kavli-configurables`` from a private MIT repository. Ensure you have proper SSH access configured.


Quick Start
-----------

Basic usage example:

.. code-block:: python

    from data_product_tracker import tracker

    # Track a data product execution
    with tracker() as t:
        # Your data processing code here
        data = process_data()

        # Register the data product
        product_id = t.register_data_product(
            name="analysis_results",
            version="1.0.0",
            metadata={"format": "parquet", "rows": len(data)}
        )

The tracker automatically captures:

* Current environment variables
* Installed Python packages and versions
* Hostname and execution context
* Timestamps and execution metadata


Database Configuration
----------------------

By default, the tracker uses an in-memory SQLite database. Configure alternative databases via environment variables or configuration files:

.. code-block:: python

    # PostgreSQL
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/dbname'

    # MySQL
    os.environ['DATABASE_URL'] = 'mysql+pymysql://user:pass@localhost/dbname'


Development
-----------

This project uses modern Python development tools:

**Testing Infrastructure**

* **Test Runner**: ``nox`` for flexible, Python-based test orchestration
* **Multi-Database Testing**: Test against SQLite, PostgreSQL, and MySQL
* **Docker Integration**: Consistent testing environment across platforms

Run tests::

    # Using Docker (recommended)
    ./scripts/docker-test.sh test

    # Test with specific database
    ./scripts/start-test-databases.sh
    ./scripts/docker-test.sh test tests-postgres

    # Run all quality checks
    nox  # runs tests, linting, type checking

**Code Quality**

* **Formatting**: ``black`` with 79-character line limit
* **Import Sorting**: ``isort`` with black-compatible profile
* **Linting**: ``flake8`` with docstring and bugbear plugins
* **Type Checking**: ``mypy`` with SQLAlchemy plugin

Format code::

    nox -s format

**Documentation**

* Testing guides in ``docs/testing-with-nox.md`` and ``docs/testing-multi-db.md``
* Semantic versioning guide in ``docs/semantic-versioning.md``
* AI assistant guidance in ``CLAUDE.md``


Contributing
------------

This project follows the Conventional Commits specification for automated semantic versioning:

* ``fix:`` for bug fixes (patch version)
* ``feat:`` for new features (minor version)
* ``feat!:`` or ``BREAKING CHANGE:`` for breaking changes (major version)

See ``docs/semantic-versioning.md`` for detailed guidelines.


Architecture
------------

The Data Product Tracker is built with:

* **SQLAlchemy 2.0+**: Modern ORM with async support
* **Click**: CLI framework for command-line tools
* **Deal**: Design-by-contract for runtime validation
* **Hypothesis**: Property-based testing

Key components:

* ``models/``: Database models for products, environments, and dependencies
* ``io/trackers.py``: High-level tracking API
* ``reflection.py``: Environment introspection and matching
* ``conn.py``: Database connection management


Credits
-------

Created by William Christopher Fong at MIT Kavli Institute.

Built with:

* SQLAlchemy for database abstraction
* nox and Docker for testing infrastructure
* Semantic Release for automated versioning

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
