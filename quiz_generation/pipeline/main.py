import os
from typing import List

from quiz_generation.evaluation.main import main as evaluate
from quiz_generation.metadata_generation.main import main as generate_metadata
from quiz_generation.pipeline.configs import (
    EvaluationConfig,
    MetadataGenerationConfig,
    QuizGenerationConfig,
    TaskConfig,
)
from quiz_generation.quiz_generation.main import main as generate_quizzes


def main(
    task_configs: List[TaskConfig],
    metadata_generation_config: MetadataGenerationConfig,
    quiz_generation_config: QuizGenerationConfig,
    evaluation_config: EvaluationConfig,
) -> None:
    for task_config in task_configs:
        os.makedirs(task_config.result_directory, exist_ok=True)
        metadata_path = os.path.join(task_config.result_directory, "metadata.json")
        quizzes_path = os.path.join(task_config.result_directory, "quizzes.jsonl")
        evaluation_path = os.path.join(
            task_config.result_directory, "evaluated_quizzes.jsonl"
        )
        generate_metadata(
            model_name=metadata_generation_config.model_name,
            connector=metadata_generation_config.connector,
            transcript_path=task_config.transcript_path,
            prompts_config=metadata_generation_config.prompts_config,
            output_path=metadata_path,
            debug=metadata_generation_config.debug,
        )
        generate_quizzes(
            model_name=quiz_generation_config.model_name,
            connector=quiz_generation_config.connector,
            transcript_path=task_config.transcript_path,
            prompts_config=quiz_generation_config.prompts_config,
            output_path=quizzes_path,
            chunks_path=task_config.chunks_path,
        )
        evaluate(
            model_name=evaluation_config.model_name,
            connector=evaluation_config.connector,
            metadata_path=metadata_path,
            quizzes_path=quizzes_path,
            language=task_config.language,
            prompts_config=evaluation_config.prompts_config,
            output_path=evaluation_path,
        )
