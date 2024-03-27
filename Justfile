set dotenv-load
set positional-arguments

# List the available recipes
default:
    @just --list

# Set up a new development environment
init:
    #!/usr/bin/env bash
    set -euxo pipefail
    if [ -e .env ]; then
        echo ".env file already exists"
    else
        cp .env.dist .env
    fi

# Install dependencies on a CPU-only development environment
install:
    uv pip install -e ".[dev]"

# Run all code checks
checks: check-deps check-lockfiles format lint type

# Check code formatting
format:
    black .
    ruff --fix .

# Run linting
lint:
    deptry .
    black --check .
    ruff check .

# Run type checking
type:
    mypy .

# Check for unused or missing dependencies
check-deps:
    deptry .

# Print a coverage report
print-cov-report:
    coverage report -m --skip-covered

# Launch all local tests, GPU tests are skipped if no GPU is available locally
test +PYTEST_OPTIONS="":
    coverage run --data-file .coverage.local_tests -m pytest "$@"

# Launch all local tests and print a coverage report
cov +PYTEST_OPTIONS="":
    coverage erase
    just test "$@"
    coverage combine
    coverage xml -o coverage.xml
    just print-cov-report
