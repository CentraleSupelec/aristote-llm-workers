import json
import os
from typing import Literal

import jsonlines

from aristote.connectors.connectors import AbstractConnector
from aristote.dtos.dtos import MetaData
from aristote.evaluation.evaluator import (
    EvaluationPromptsConfig,
    Evaluator,
    MultipleAnswerQuiz,
)
from aristote.preprocessing.preprocessing import get_tokenizer


def main(
    model_name: str,
    connector: AbstractConnector,
    metadata_path: str,
    quizzes_path: str,
    language: Literal["en", "fr"],
    prompts_config: EvaluationPromptsConfig,
    output_path: str,
) -> None:
    tokenizer = get_tokenizer(model_name)

    with open(metadata_path, "r", encoding="utf-8") as file:
        course_metadata = json.load(file)

    quizzes = []
    with jsonlines.open(quizzes_path, "r") as reader:
        for line in reader:
            quizzes.append(MultipleAnswerQuiz(**line))

    evaluator = Evaluator(
        model_name=model_name,
        course_metadata=MetaData(**course_metadata),
        tokenizer=tokenizer,
        connector=connector,
        language=language,
        prompts_config=prompts_config,
    )
    evaluated_quizzes = evaluator.evaluate_quizzes(quizzes)

    with jsonlines.open(output_path, "w") as writer:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        for evaluated_quiz in evaluated_quizzes:
            writer.write(evaluated_quiz.model_dump(mode="json"))
