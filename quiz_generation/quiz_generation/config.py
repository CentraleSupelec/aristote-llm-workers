from pydantic import BaseModel

from quiz_generation.quiz_generation.quiz_generator import QuizPromptsConfig


class QuizMainConfig(BaseModel):
    model_name: str
    metadata_path: str
    transcript_path: str
    output_path: str
    cache_path: str
    prompts_config: QuizPromptsConfig
