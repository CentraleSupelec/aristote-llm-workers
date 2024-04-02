# Aristote - Quiz Generation

Aristote is an educacional assistant that uses open-source LLMs to describe educational video transcripts and generate quizzes to help students learn.

You can send a video transcript to Aristote and Aristote will generate the title, the description, a list of topics covered in the video and the main discipline of the video. It can also generate a list of potential quizzes on the different topics of the video. These quizzes can have several flaws. So we try to generate as much quizzes as possible so that a human can select the best quizzes and have as much new quiz ideas as possible.

If you want to accelerate the selection of the quizzes generated with the open-source LLMs, you can use Aristote to evaluate your quizzes with GPT-4 according to several specific boolean criteria and filter out bad quizzes based on this evaluation:

- whether the question is really a question,
- whether the question is related to the subject of the course,
- whether the question is self contained,
- whether the language is clear,
- whether the answers are all different,
- whether the answers are related,
- whether the fake answers are not obvious,
- whether the quiz is about a theoretical concept or a specific course example.

**Table of Contents**

- [How does it work?](#how-does-it-work)
- [Getting Started: Use Aristote with Docker (Recommended)](#getting-started-use-aristote-with-docker-recommended)
  - [Use `docker-compose` (Recommended)](#use-docker-compose-recommended)
  - [Launch separatly](#launch-separatly)
    - [LLM Service](#llm-service)
    - [Quiz Generation Service](#quiz-generation-service)
- [Use Aristote's CLI](#use-aristotes-cli)
  - [Generate metadata](#generate-metadata)
  - [Generate quizzes](#generate-quizzes)
- [Contributing](#contributing)
- [Credits](#credits)

## How does it work?

Aristote generates quizzes and metadata from the transcript of a video.

For the metadata generation, it splits the video transcript into chunks. Then each chunk is rewritten with the LLM to have a nicely written text. Each chunk is transformed into a summary of the chunk. Then a title, a description and other metadata are extracted from this set of summaries.

Quizzes are generated using the same principle. One quiz is generated from each rewritten chunk. This time, the transcript is split into chunks of different length, which implies that text might appear several times in different chunks. The objective is to have quizzes about local and global transcript information and have as much quizzes as possible so that we can have as much quizzes as possible to choose from. Each quiz can be evaluated using an OpenAI model and the title and description of the quiz.

This diagram shows how the pipeline works:

![img](assets/pipeline.png)

## Getting Started: Use Aristote with Docker (Recommended)

Aristote is based on two services. One service deploys the LLM through a vLLM server. The other manages the metadata and quiz generation by calling the LLM.

**VM Specs to launch the service:** Make sure you have the adapted hardware to run Aristote. You will need at least 16GB of GPU VRAM to deploy OpenHermes Mistral 7B.

### Use `docker-compose` (Recommended)

First set up your `.env` file based on the `.env.dist` file.

Then you can launch the quiz generation API. You can use the following command:

```bash
docker compose up
```

To get the documentation of the API, you can go to the `/docs` route of the API.

### Launch separatly

You can launch the LLM service and the Metadata/Quiz Generation service separately.

#### LLM Service

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

#### Quiz Generation Service

```bash
docker build -t aristote -f server/Dockerfile . && docker run --env-file .env --network="host" -p 3000:3000 aristote
```

**Warning:** `--network="host"` only works on Linux.

## Use Aristote's CLI

You can test the features of the app without Docker.

You can do it, locally, through the `aristote` cli.
In a virtual environment, we recommend installing dependencies with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -e .
```

But you can also simply install the dependencies with `pip`.

```bash
pip install -e .
```

You also have to set up your `.env` file based on the `.env.dist` file.

### Generate metadata

First configure your `yml` file for this generation based on the [provided example](configs/zephyr_fr/metadata_generation.yml).

Then launch the following command with your config file path:

```bash
aristote generate-metadata {METADATA_YML_CONFIG_PATH}
```

Example of config [here](configs/metadata_generation.yml).

### Generate quizzes

First configure your `yml` file for this generation based on the [provided example](configs/zephyr_fr/quiz_generation.yml).

Then launch the following command with your config file path:

```bash
aristote generate-quizzes {QUIZ_GEN_YML_CONFIG_PATH}
```

Example of config [here](configs/quiz_generation.yml).

## Contributing

To contribute, we recommend to install the [`just`](https://github.com/casey/just) command.

Then you can setup the dev dependencies with:

```bash
just intall
```

Launch tests with:

```bash
just test
```

Check linting with:

```bash
just lint
```

And reformat files with:

```bash
just format
```

## Credits

This project is based on a prototype made by four students from the [Paris Digital Lab](https://paris-digital-lab.com/): Antoine Vaglio, Liwei Sun, Mohammed Bahhad et Pierre-Louis Veyrenc.

Illuin Technology perfected the project and made it available as it is now for CentraleSupélec.
