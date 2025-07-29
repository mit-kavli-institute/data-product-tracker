#!/bin/bash
# Docker wrapper script for running nox tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  test [SESSION]    Run nox tests (default: all sessions)"
    echo "  shell             Open interactive shell in container"
    echo "  docs              Build and serve documentation"
    echo "  clean             Clean up Docker containers and volumes"
    echo "  build             Build Docker image"
    echo ""
    echo "Test Sessions:"
    echo "  tests             Run pytest across all Python versions"
    echo "  lint              Run flake8 linting"
    echo "  format            Format code with black and isort"
    echo "  typecheck         Run mypy type checking"
    echo "  coverage          Generate coverage report"
    echo "  safety            Check for security vulnerabilities"
    echo ""
    echo "Examples:"
    echo "  $0 test           # Run all default sessions"
    echo "  $0 test tests     # Run only pytest"
    echo "  $0 test lint      # Run only linting"
    echo "  $0 shell          # Open bash shell in container"
}

# Parse command
COMMAND=${1:-test}
shift || true

case "$COMMAND" in
    test)
        SESSION=${1:-}
        if [ -n "$SESSION" ]; then
            print_color "$YELLOW" "Running nox session: $SESSION"
            docker-compose run --rm nox nox -s "$SESSION"
        else
            print_color "$YELLOW" "Running all default nox sessions"
            docker-compose run --rm test-runner
        fi
        ;;

    shell)
        print_color "$YELLOW" "Opening shell in test container"
        docker-compose run --rm dev
        ;;

    docs)
        print_color "$YELLOW" "Building and serving documentation"
        docker-compose up docs
        ;;

    build)
        print_color "$YELLOW" "Building Docker image"
        docker-compose build test-runner
        ;;

    clean)
        print_color "$YELLOW" "Cleaning up Docker containers and volumes"
        docker-compose down -v
        ;;

    help|--help|-h)
        usage
        exit 0
        ;;

    *)
        print_color "$RED" "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
