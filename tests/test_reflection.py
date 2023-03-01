import os

import pytest  # noqa 401
import sqlalchemy as sa

from data_product_tracker.models import environment as e
from data_product_tracker.reflection import get_or_create_env


def test_reflection_of_environment(database):
    env_id, _ = get_or_create_env(database)
    with database as db:
        q = sa.select(e.Environment).where(e.Environment.id == env_id)
        environment = db.execute(q).scalars().first()
        for variable in environment.variables:
            assert variable.value == os.environ[variable.key]
