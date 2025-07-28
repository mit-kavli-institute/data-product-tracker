#!/bin/bash
# Script to check documentation builds without warnings

set -e

echo "Building documentation with strict mode..."
echo "========================================="

# Build docs with warnings as errors
docker-compose run --rm test-runner nox -s docs

echo ""
echo "Documentation build completed successfully!"
echo ""
echo "To view the documentation locally, run:"
echo "  docker-compose up docs"
echo "Or:"
echo "  nox -s docs -- serve"
