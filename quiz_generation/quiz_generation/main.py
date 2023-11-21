import json
from typing import Literal

import jsonlines

from quiz_generation.connectors.connectors import AbstractConnector
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.preprocessing.preprocessing import get_tokenizer, load_file
from quiz_generation.quiz_generation.quiz_generator import (
    QuizGenerator,
    QuizPromptsConfig,
)


def main(
    model_name: str,
    connector: AbstractConnector,
    transcript_path: str,
    language: Literal["en", "fr"],
    prompts_config: QuizPromptsConfig,
    output_path: str,
) -> None:
    tokenizer = get_tokenizer(model_name)

    transcripts = load_file(transcript_path)

    quiz_generator = QuizGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        language=language,
        prompts_config=prompts_config,
    )
    quizzes = quiz_generator.full_generation(transcripts)

    with jsonlines.open(output_path, "w") as writer:
        for quiz in quizzes:
            writer.write(quiz.model_dump(mode="json"))
