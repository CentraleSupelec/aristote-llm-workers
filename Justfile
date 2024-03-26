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
install-cpu:
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cpu
    pdm sync --dev -G :all -L lockfiles/cpu.lock

# Install dependencies on an Nvidia GPU development environment
install-gpu: 
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cu117
    pdm sync --dev -G :all -L lockfiles/gpu.lock

# Refresh lockfiles
refresh-lockfiles:
    #!/usr/bin/env bash
    set -euxo pipefail
    export LOCAL_TORCH_INDEX_URL=$(pdm config pypi.torch.url)
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cu117
    pdm update --update-reuse --no-sync -L lockfiles/gpu.lock -G :all
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cpu
    pdm update --update-reuse --no-sync -L lockfiles/cpu.lock -G :all
    pdm config --local pypi.torch.url $LOCAL_TORCH_INDEX_URL
    if [ "$LOCAL_TORCH_INDEX_URL" == "https://download.pytorch.org/whl/cpu" ]; then \
        just install-cpu; \
    else \
        just install-gpu; \
    fi

# Add one or multiple dependencies to a dependency group
add +PDM_OPTIONS="":
    #!/usr/bin/env bash
    set -euxo pipefail
    export LOCAL_TORCH_INDEX_URL=$(pdm config pypi.torch.url)
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cu117
    pdm add "$@" --update-reuse --no-sync -L lockfiles/gpu.lock
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cpu
    pdm add "$@" --update-reuse --no-sync -L lockfiles/cpu.lock
    pdm config --local pypi.torch.url $LOCAL_TORCH_INDEX_URL
    if [ "$LOCAL_TORCH_INDEX_URL" == "https://download.pytorch.org/whl/cpu" ]; then \
        just install-cpu; \
    else \
        just install-gpu; \
    fi

# Remove one or multiple dependencies from a dependency group
remove +PDM_OPTIONS="":
    #!/usr/bin/env bash
    set -euxo pipefail
    pdm remove "$@" --no-sync
    just refresh-lockfiles

# Upgrade one or multiple dependencies from a dependency group
upgrade +PDM_OPTIONS="":
    #!/usr/bin/env bash
    set -euxo pipefail
    export LOCAL_TORCH_INDEX_URL=$(pdm config pypi.torch.url)
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cu117
    pdm update "$@" --no-sync -L lockfiles/gpu.lock
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cpu
    pdm update "$@" --no-sync -L lockfiles/cpu.lock
    pdm config --local pypi.torch.url $LOCAL_TORCH_INDEX_URL
    if [ "$LOCAL_TORCH_INDEX_URL" == "https://download.pytorch.org/whl/cpu" ]; then \
        just install-cpu; \
    else \
        just install-gpu; \
    fi

# Upgrade all dependencies
upgrade-all:
    #!/usr/bin/env bash
    set -euxo pipefail
    export LOCAL_TORCH_INDEX_URL=$(pdm config pypi.torch.url)
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cu117
    pdm update --update-all --no-sync --dev -G :all -L lockfiles/gpu.lock --no-sync
    pdm config --local pypi.torch.url https://download.pytorch.org/whl/cpu
    pdm update --update-all --no-sync --dev -G :all -L lockfiles/cpu.lock --no-sync
    pdm config --local pypi.torch.url $LOCAL_TORCH_INDEX_URL
    if [ "$LOCAL_TORCH_INDEX_URL" == "https://download.pytorch.org/whl/cpu" ]; then \
        just install-cpu; \
    else \
        just install-gpu; \
    fi

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

# Check if the lock file is up to date
check-lockfiles:
    pdm lock --check -L lockfiles/cpu.lock
    pdm lock --check -L lockfiles/gpu.lock

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
