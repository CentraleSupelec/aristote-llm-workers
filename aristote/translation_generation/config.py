from pydantic import BaseModel

from aristote.translation_generation.translation_generator import (
    TranslationPromptsConfig,
)


class TranslationMainConfig(BaseModel):
    model_name: str
    transcript_path: str
    output_path: str
    cache_path: str
    prompts_config: TranslationPromptsConfig
