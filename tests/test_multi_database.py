"""Tests for multi-database support."""

import pytest
import sqlalchemy as sa

from data_product_tracker.libraries import Distribution
from data_product_tracker.models import environment as e
from data_product_tracker.reflection import (
    get_or_create_env,
    reflect_libraries,
    reflect_variables,
)
from data_product_tracker.variables import OSVariable


class TestMultiDatabase:
    """Test suite that runs against multiple database types."""

    def test_database_connection(self, multi_db_session, database_config):
        """Test basic database connectivity."""
        # This test will run once for each configured database
        result = multi_db_session.execute(sa.text("SELECT 1")).scalar()
        assert result == 1

        # Log which database we're testing
        print(f"\nTesting with {database_config.name}")

    def test_basic_operations(self, multi_db_session):
        """Test basic CRUD operations across databases."""
        # Create a variable
        var = e.Variable(key="TEST_KEY", value="TEST_VALUE")
        multi_db_session.add(var)
        multi_db_session.commit()

        # Read it back
        found = multi_db_session.scalar(
            sa.select(e.Variable).where(e.Variable.key == "TEST_KEY")
        )
        assert found is not None
        assert found.value == "TEST_VALUE"

        # Update it
        found.value = "UPDATED_VALUE"
        multi_db_session.commit()

        # Verify update
        updated = multi_db_session.scalar(
            sa.select(e.Variable).where(e.Variable.key == "TEST_KEY")
        )
        assert updated.value == "UPDATED_VALUE"

        # Delete it
        multi_db_session.delete(updated)
        multi_db_session.commit()

        # Verify deletion
        deleted = multi_db_session.scalar(
            sa.select(e.Variable).where(e.Variable.key == "TEST_KEY")
        )
        assert deleted is None

    def test_reflection_with_multi_db(self, multi_db_session):
        """Test reflection functionality across databases."""
        # Test variable reflection
        os_vars = [
            OSVariable(key="PATH", value="/usr/bin:/bin"),
            OSVariable(key="HOME", value="/home/test"),
        ]
        var_ids = reflect_variables(multi_db_session, os_vars)
        assert len(var_ids) == 2

        # Test library reflection
        distributions = [
            Distribution(name="pytest", version="7.0.0"),
            Distribution(name="sqlalchemy", version="2.0.0"),
        ]
        lib_ids = reflect_libraries(multi_db_session, distributions)
        assert len(lib_ids) == 2

        # Test environment creation
        env_id, created = get_or_create_env(
            multi_db_session,
            environ=os_vars,
            distributions=distributions,
        )
        assert created is True
        assert env_id is not None

        # Test that getting the same environment returns existing
        env_id2, created2 = get_or_create_env(
            multi_db_session,
            environ=os_vars,
            distributions=distributions,
        )
        assert created2 is False
        assert env_id2 == env_id

    @pytest.mark.postgres
    def test_postgres_specific_feature(
        self, multi_db_session, database_config
    ):
        """Test PostgreSQL-specific features."""
        if database_config.dialect != "postgresql":
            pytest.skip("PostgreSQL-specific test")

        # Test PostgreSQL array types or other PG-specific features
        result = multi_db_session.execute(sa.text("SELECT version()")).scalar()
        assert "PostgreSQL" in result

    @pytest.mark.slow
    def test_bulk_operations(self, multi_db_session):
        """Test bulk operations that might be slow on some databases."""
        # Create many variables
        variables = [
            e.Variable(key=f"KEY_{i}", value=f"VALUE_{i}") for i in range(100)
        ]
        multi_db_session.add_all(variables)
        multi_db_session.commit()

        # Verify all were created
        count = multi_db_session.scalar(
            sa.select(sa.func.count()).select_from(e.Variable)
        )
        assert count >= 100  # >= because there might be other data


# Test using the original fixtures (backward compatibility)
def test_original_fixtures_still_work(db_session):
    """Ensure original SQLite fixtures still work."""
    # This uses the original db_session fixture
    var = e.Variable(key="COMPAT_TEST", value="WORKS")
    db_session.add(var)
    db_session.commit()

    found = db_session.scalar(
        sa.select(e.Variable).where(e.Variable.key == "COMPAT_TEST")
    )
    assert found is not None
    assert found.value == "WORKS"
