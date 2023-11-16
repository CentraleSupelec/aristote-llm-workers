import json
from typing import Literal

import jsonlines
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import AbstractConnector
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.preprocessing.preprocessing import load_file
from quiz_generation.quiz_generation.quiz_generator import (
    QuizGenerator,
    QuizPromptsConfig,
)

API_URL = "http://0.0.0.0:8000/generate"


def main(
    model_name: str,
    connector: AbstractConnector,
    metadata_path: str,
    transcript_path: str,
    language: Literal["en", "fr"],
    prompts_config: QuizPromptsConfig,
    output_path: str,
) -> None:
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    transcripts = load_file(transcript_path)

    with open(metadata_path, "r", encoding="utf-8") as file:
        course_metadata = json.load(file)

    quiz_generator = QuizGenerator(
        model_name=model_name,
        course_metadata=MetaData(**course_metadata),
        tokenizer=tokenizer,
        api_connector=connector,
        language=language,
        prompts_config=prompts_config,
    )
    quizzes = quiz_generator.full_generation(transcripts)

    with jsonlines.open(output_path, "w") as writer:
        for quiz in quizzes:
            writer.write(quiz.model_dump(mode="json"))
