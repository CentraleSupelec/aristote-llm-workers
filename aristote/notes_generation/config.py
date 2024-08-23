from pydantic import BaseModel

from aristote.notes_generation.notes_generator import NotesPromptsConfig


class NotesMainConfig(BaseModel):
    model_name: str
    transcript_path: str
    output_path: str
    cache_path: str
    prompts_config: NotesPromptsConfig
