from typing import Callable

import click
import configue

from quiz_generation.metadata_generation.main import main as metadata_main
from quiz_generation.quiz_generation.main import main as quiz_main

API_URL = "http://0.0.0.0:8000/generate"


@click.group()
def main() -> None:
    pass


def base_command(config_path: str, command_function: Callable) -> None:
    config = configue.load(config_path)
    command_function(**config)


@main.command()
@click.argument("config_path", type=str)
def generate_metadata(config_path: str) -> None:
    base_command(config_path, metadata_main)


@main.command()
@click.argument("config_path", type=str)
def generate_quizzes(config_path: str) -> None:
    base_command(config_path, quiz_main)
