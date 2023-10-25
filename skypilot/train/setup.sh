#!/bin/bash

set -e

echo "Building Docker image..."
docker buildx build \
    -t llm-core-gpu:dev \
    --build-arg DEVICE=gpu \
    --build-arg NEXUS_PYPI_PULL_URL=${NEXUS_PYPI_PULL_URL} \
    --target dev-stage \
    .  
