from typing import List, Optional

import jsonlines

from aristote.connectors.connectors import AbstractConnector
from aristote.preprocessing.preprocessing import get_tokenizer, load_file
from aristote.quiz_generation.quiz_generator import (
    MultipleAnswerQuiz,
    QuizGenerator,
    QuizPromptsConfig,
)


def main(
    model_name: str,
    connector: AbstractConnector,
    transcript_path: str,
    prompts_config: QuizPromptsConfig,
    output_path: str,
    chunks_path: Optional[str] = None,
) -> List[MultipleAnswerQuiz]:
    tokenizer = get_tokenizer(model_name)

    transcripts = load_file(transcript_path)

    quiz_generator = QuizGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        chunks_path=chunks_path,
    )
    quizzes = quiz_generator.full_generation(transcripts)

    with jsonlines.open(output_path, "w") as writer:
        for quiz in quizzes:
            writer.write(quiz.model_dump(mode="json"))

    return quizzes
