from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel

from quiz_generation.connectors.connectors import AbstractConnector
from quiz_generation.evaluation.evaluator import EvaluationPromptsConfig
from quiz_generation.metadata_generation.metadata_generator import MetadataPromptsConfig
from quiz_generation.quiz_generation.quiz_generator import QuizPromptsConfig


@dataclass
class MetadataGenerationConfig:
    model_name: str
    connector: AbstractConnector
    prompts_config: MetadataPromptsConfig
    debug: bool


@dataclass
class QuizGenerationConfig:
    model_name: str
    connector: AbstractConnector
    prompts_config: QuizPromptsConfig


@dataclass
class EvaluationConfig:
    model_name: str
    connector: AbstractConnector
    prompts_config: EvaluationPromptsConfig


class TaskConfig(BaseModel):
    transcript_path: str
    result_directory: str
    language: Literal["en", "fr"]
    chunks_path: Optional[str] = None
