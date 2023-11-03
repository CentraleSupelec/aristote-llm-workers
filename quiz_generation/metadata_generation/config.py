from pydantic import BaseModel

from quiz_generation.metadata_generation.metadata_generator import MetadataPromptsConfig


class MetadataMainConfig(BaseModel):
    model_name: str
    transcript_path: str
    output_path: str
    cache_path: str
    prompts_config: MetadataPromptsConfig
