#!/bin/bash
# Start test database services and wait for them to be ready

set -e

echo "Starting test database services..."

# Start the database services
docker compose up -d postgres-16 postgres-14 mysql-8 mariadb-11

echo "Waiting for databases to be ready..."

# Wait for PostgreSQL 16
echo -n "Waiting for PostgreSQL 16..."
until docker compose exec -T postgres-16 pg_isready -U testuser -d testdb >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " Ready!"

# Wait for PostgreSQL 14
echo -n "Waiting for PostgreSQL 14..."
until docker compose exec -T postgres-14 pg_isready -U testuser -d testdb >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " Ready!"

# Wait for MySQL 8
echo -n "Waiting for MySQL 8..."
until docker compose exec -T mysql-8 mysqladmin ping -h localhost -u root -prootpass >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " Ready!"

# Wait for MariaDB 11
echo -n "Waiting for MariaDB 11..."
until docker compose exec -T mariadb-11 healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " Ready!"

echo ""
echo "All database services are ready!"
echo ""
echo "You can now run tests with:"
echo "  ./scripts/docker-test.sh test tests-postgres    # Test PostgreSQL"
echo "  ./scripts/docker-test.sh test tests-mysql       # Test MySQL/MariaDB"
echo "  ./scripts/docker-test.sh test tests-all-databases  # Test all databases"
echo ""
echo "To stop the databases:"
echo "  docker compose down"
