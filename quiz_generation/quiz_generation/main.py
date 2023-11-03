import json

import click
import configue
import jsonlines
from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.quiz_generation.quiz_generator import QuizGenerator

API_URL = "http://0.0.0.0:8000/generate"


@click.command()
@click.option("--config_path", type=str, help="Path to the configuration file.")
def main(config_path: str) -> None:
    config = configue.load(config_path)
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    api_connector = APIConnector(API_URL, config.cache_path)

    with open(config.metadata_path, "r", encoding="utf-8") as file:
        course_metadata = json.load(file)

    with open(config.transcript_path, "r", encoding="utf-8") as file:
        transcripts = json.load(file)["transcripts"]

    quiz_generator = QuizGenerator(
        model_name=config.model_name,
        course_metadata=MetaData(**course_metadata),
        tokenizer=tokenizer,
        api_connector=api_connector,
        prompts_config=config.prompts_config,
    )
    quizzes = quiz_generator.full_generation(transcripts)

    with jsonlines.open(config.output_path, "w") as writer:
        for quiz in quizzes:
            writer.write(quiz.model_dump(mode="json"))


if __name__ == "__main__":
    main()
