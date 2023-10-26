# Which accelerator to target. Can be "cpu" or "gpu"
ARG DEVICE="cpu"

# Flags to pass to the `pdm sync` command
# Useful to build images that can be used for internal testing and development
ARG PDM_SYNC_FLAGS="--prod"

# Nexus credential necessary to install internal packages
ARG NEXUS_PYPI_PULL_URL

# PDM version to use
ARG PDM_VERSION="2.9.2"


#######################################################################################################################
#
# GPU RUNNER STAGE
#
#######################################################################################################################

FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime as gpu-runner
RUN apt-get update --yes --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*
ARG PDM_VERSION
RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python - --version v${PDM_VERSION}
ENV PATH="/root/.local/bin:$PATH"
RUN pdm config venv.backend conda && pdm use -f /opt/conda
ENV CUDART_PATH="/opt/conda/lib/"


#######################################################################################################################
#
# CPU RUNNER STAGE
#
#######################################################################################################################

FROM python:3.10.11-slim as cpu-runner
RUN apt-get update --yes --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*
ARG PDM_VERSION
RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python - --version v${PDM_VERSION}
ENV PATH="/root/.local/bin:$PATH"
RUN python -m venv /opt/.venv && pdm use -f /opt/.venv
RUN . /opt/.venv/bin/activate && \
    pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu
ENV PATH="/opt/.venv/bin:$PATH"


#######################################################################################################################
#
# DEVELOPMENT STAGE
#
# This stage serves as a runner during development to accelerate the build time. The project's root should be mounted
# inside /workspace using the flag: -v $(pwd):/workspace/
#
#######################################################################################################################


FROM ${DEVICE}-runner as dev-stage
ENV PYTHONUNBUFFERED=1
ENV BITSANDBYTES_NOWELCOME="1"
ENV TOKENIZERS_PARALLELISM="false"
ENV TRANSFORMERS_NO_ADVISORY_WARNINGS="true"
ENV HF_DATASETS_CACHE="/root/.cache/huggingface/datasets"
RUN apt-get update --yes --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*
ARG DEVICE
COPY pyproject.toml lockfiles/pdm-${DEVICE}.lock ./
ARG NEXUS_PYPI_PULL_URL
RUN pdm config pypi.extra.url "$NEXUS_PYPI_PULL_URL"
ARG PDM_SYNC_FLAGS
RUN pdm install --no-self -L pdm-${DEVICE}.lock ${PDM_SYNC_FLAGS}
WORKDIR /workspace
CMD [ "python", "--version" ]
