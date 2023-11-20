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
