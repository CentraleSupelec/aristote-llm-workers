# Aristote - Quiz Generation

Aristote is an educacional assistant that uses open-source LLMs to describe educacional video transcripts and generate quizzes to help students learn.

You can send a video transcript to Aristote and Aristote will generate the title, the description, a list of topics covered in the video and the main discipline of the video. It can also generate a list of potential quizzes on the different topics of the video.

If you want to accelerate the selection of the quizzes generated with the open-source LLMs, you can use Aristote to evaluate your quizzes with GPT-4 according to several specific boolean criteria and filter out bad quizzes based on this evaluation:

- whether the question is really a question,
- whether the question is related to the subject of the course,
- whether the question is self contained,
- whether the language is clear,
- whether the answers are all different,
- whether the answers are related,
- whether the fake answers are not obvious,
- whether the quiz is about a theoretical concept or a specific course example.

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

You can launch the VLLM API and the Quiz Generation API separately.

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

**Warning:** `--network="host"` only works on Linux.

## Credits

This project is based on a prototype made by four students from the [Paris Digital Lab](https://paris-digital-lab.com/): Antoine Vaglio, Liwei Sun, Mohammed Bahhad et Pierre-Louis Veyrenc.

Illuin Technology perfected the project and made it available as it is now for CentraleSupélec.
