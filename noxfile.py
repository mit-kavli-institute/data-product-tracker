"""Nox configuration for data_product_tracker."""

from pathlib import Path

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.11", "3.12"]

# Source directories
SRC_DIR = Path("src/data_product_tracker")
TESTS_DIR = Path("tests")
DOCS_DIR = Path("docs")

# Default sessions to run
nox.options.sessions = ["tests", "lint", "typecheck"]


def install_dpt(session, *flags: str):
    session.install(
        *flags,
        "--extra-index-url",
        "https://mit-kavli-institute.github.io/MIT-Kavli-PyPi/",
    )


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite with pytest."""
    install_dpt(session, "-e", ".[dev]")
    session.install(
        "pytest", "pytest-cov", "pytest-sugar", "hypothesis", "pytest-xdist"
    )

    # Run tests with SQLite in-memory database
    # Note: Using -n auto with SQLite requires proper fixture isolation
    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
        "--dist=loadscope",  # Group tests by module for SQLite compat
        "-n",
        "auto",
        *session.posargs,
    )


@nox.session(python="3.11")
def tests_postgres(session):
    """Run tests against PostgreSQL databases."""
    install_dpt(session, "-e", ".[dev]")
    session.install(
        "pytest", "pytest-cov", "pytest-sugar", "hypothesis", "pytest-xdist"
    )

    # Set environment to use PostgreSQL
    session.env["TEST_DATABASES"] = "postgres"
    session.env["IN_DOCKER"] = "true"  # Assume we're in Docker environment

    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "-v",
        "--database=postgres-16",
        "--database=postgres-14",
        *session.posargs,
    )


@nox.session(python="3.11")
def tests_mysql(session):
    """Run tests against MySQL/MariaDB databases."""
    install_dpt(session, "-e", ".[dev]")
    session.install(
        "pytest",
        "pytest-cov",
        "pytest-sugar",
        "hypothesis",
        "pytest-xdist",
        "pymysql",  # MySQL driver
    )

    # Set environment to use MySQL
    session.env["IN_DOCKER"] = "true"

    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "-v",
        "--database=mysql-8",
        "--database=mariadb-11",
        *session.posargs,
    )


@nox.session(python="3.11")
def tests_all_databases(session):
    """Run tests against all configured databases."""
    install_dpt(session, "-e", ".[dev]")
    session.install(
        "pytest",
        "pytest-cov",
        "pytest-sugar",
        "hypothesis",
        "pytest-xdist",
        "pymysql",  # For MySQL support
    )

    # Set environment
    session.env["IN_DOCKER"] = "true"

    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
        "--all-databases",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS)
def tests_serial(session):
    """Run the test suite with pytest in serial mode (no parallelization)."""
    install_dpt(session, "-e", ".[dev]")
    session.install("pytest", "pytest-cov", "pytest-sugar", "hypothesis")

    # Run tests serially - useful for debugging parallel issues
    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
        *session.posargs,
    )


@nox.session(python="3.11")
def lint(session):
    """Run flake8 linting."""
    session.install("flake8", "flake8-docstrings", "flake8-bugbear")
    session.run("flake8", str(SRC_DIR))


@nox.session(python="3.11")
def format(session):
    """Format code with black and isort."""
    session.install("black", "isort")

    # Run formatters
    session.run("black", str(SRC_DIR), str(TESTS_DIR), *session.posargs)
    session.run("isort", str(SRC_DIR), str(TESTS_DIR), *session.posargs)


@nox.session(python="3.11")
def typecheck(session):
    """Run mypy type checking."""
    install_dpt(session, "-e", ".[dev]")
    session.install("mypy", "sqlalchemy[mypy]", "types-click")
    session.run("mypy", "--install-types", "--non-interactive", str(SRC_DIR))


@nox.session(python="3.11")
def docs(session):
    """Build documentation with Sphinx."""
    install_dpt(session, "-e", ".[dev]")
    session.install("sphinx", "sphinx-rtd-theme")

    # Build docs
    session.run(
        "sphinx-build", "-M", "html", str(DOCS_DIR), str(DOCS_DIR / "_build")
    )

    # Serve docs if requested
    if session.posargs and session.posargs[0] == "serve":
        session.log("Serving documentation at http://localhost:8000")
        session.cd(str(DOCS_DIR / "_build" / "html"))
        session.run("python", "-m", "http.server", "8000")


@nox.session(python="3.11")
def coverage(session):
    """Run tests with coverage and generate reports."""
    install_dpt(session, "-e", ".[dev]")
    session.install(
        "pytest", "pytest-cov", "pytest-sugar", "hypothesis", "coverage[toml]"
    )

    # Run tests with coverage
    session.run(
        "pytest",
        "--cov=data_product_tracker",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
        *session.posargs,
    )

    # Also generate a text report
    session.run("coverage", "report")

    # Open in browser if requested
    if session.posargs and session.posargs[0] == "open":
        import webbrowser

        webbrowser.open(str(Path("htmlcov/index.html").absolute()))


@nox.session(python="3.11")
def clean(session):
    """Clean up generated files."""
    import shutil

    # Directories to clean
    dirs_to_clean = [
        ".coverage",
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "build",
        "dist",
        "*.egg-info",
        "docs/_build",
    ]

    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                session.log(f"Removing directory: {path}")
                shutil.rmtree(path)
            else:
                session.log(f"Removing file: {path}")
                path.unlink()


@nox.session(python="3.11")
def dev(session):
    """Install the package in development mode."""
    install_dpt(session, "-e", ".[dev]")
    session.log("Development environment ready!")


@nox.session(python=PYTHON_VERSIONS)
def safety(session):
    """Check for security vulnerabilities in dependencies."""
    session.install("safety")
    session.run("safety", "check", "--full-report")
