# Quiz Generation

Generate quizzes with Large Language Models for educational purposes.

## Install

You can install the dependencies with `pdm` or `pip` depending on your preference.

### `pip` install

```bash
pip install -e .
```

### `pdm` install

```bash
pdm sync --dev -G :all -L lockfiles/{DEVICE}.lock
```

where `{DEVICE}` is the type of device you are using. You can choose between `cpu` and `gpu`.

### Load the data

To download the data, you need `dvc`. Check the install procedure [here](https://dvc.org/doc/install).

Make sure that you have access to the `gs://quiz-generation` bucket in the `llm-testing` project. Then, you can download the data with:

```bash
dvc pull
```

## Generate metadata

First configure your `yml` file for this generation based on the [provided example](configs/zephyr_fr/metadata_generation.yml).

Then launch the following command with your config file path:

```bash
quizgen generate-metadata {METADATA_YML_CONFIG_PATH}
```

## Generate quizzes

First configure your `yml` file for this generation based on the [provided example](configs/zephyr_fr/quiz_generation.yml).

Then launch the following command with your config file path:

```bash
quizgen generate-quizzes {QUIZ_GEN_YML_CONFIG_PATH}
```

## Launch Quiz Generation API with Docker 

First set up your `.env` file based on the `.env.dist` file.

Then you can launch the quiz generation API. You can use the following command by replacing `{NEXUS_PYPI_PULL_URL}` with your URL of the Nexus PyPI repository:

```bash
NEXUS_PYPI_PULL_URL={NEXUS_PYPI_PULL_URL} docker compose up
```

To get the documentation of the API, you can go to the `docs` route of the API.

### VM Specs to launch the service

You will need at least 32 GB of GPU VRAM to launch the service.

### Launch seperatly

You can launch the VLLM API and the Quiz Generation API seperatly.

#### VLLM API

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:v0.2.4 \
    --model teknium/OpenHermes-2.5-Mistral-7B \
    --dtype float16 \
    --tensor-parallel-size 2
```

#### Quiz Generation API

```bash
docker build --build-arg="NEXUS_PYPI_PULL_URL={NEXUS_PYPI_PULL_URL}" -t quizgen -f server/Dockerfile . && docker run --env-file .env --network="host" -p 3000:3000 quizgen
```
