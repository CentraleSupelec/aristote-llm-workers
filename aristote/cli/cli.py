import os
from typing import Callable

import click
import configue

os.environ["TRANSFORMERS_VERBOSITY"] = "error"  # noqa: E402
from aristote.evaluation.main import main as evaluation_main
from aristote.metadata_generation.main import main as metadata_main
from aristote.notes_generation.main import main as notes_main
from aristote.pipeline.main import main as pipeline_main
from aristote.quiz_generation.main import main as quiz_main
from aristote.translation_generation.main import main as translation_main

API_URL = "http://0.0.0.0:8000/generate"


@click.group()
def main() -> None:
    pass


def base_command(config_path: str, command_function: Callable) -> None:
    config = configue.load(config_path)
    command_function(**config)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def generate_metadata(config_path: str) -> None:
    """Generate metadata from transcripts file

    Args:
        CONFIG_PATH (str): Path to YAML metadata generation config.
    """
    base_command(config_path, metadata_main)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def generate_quizzes(config_path: str) -> None:
    """Generate quizzes from transcripts file

    Args:
        CONFIG_PATH (str): Path to YAML quizzes generation config.
    """
    base_command(config_path, quiz_main)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def evaluate(config_path: str) -> None:
    """Evaluate quizzes from transcripts file and metadata

    Args:
        CONFIG_PATH (str): Path to YAML evaluation config.
    """
    base_command(config_path, evaluation_main)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def generate_notes(config_path: str) -> None:
    """Generate notes from transcripts file and metadata

    Args:
        CONFIG_PATH (str): Path to YAML note generation config.
    """
    base_command(config_path, notes_main)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def translate(config_path: str) -> None:
    """Translate metadata, quizzes, notes and transcripts

    Args:
        CONFIG_PATH (str): Path to YAML translation config.
    """
    base_command(config_path, translation_main)


@main.command()
@click.argument(
    "config_path",
    type=str,
)
def pipeline(config_path: str) -> None:
    """Generate metadata and quizzes from several transcripts files

    Args:
        CONFIG_PATH (str): Path to YAML genration pipeline config.
    """
    base_command(config_path, pipeline_main)
