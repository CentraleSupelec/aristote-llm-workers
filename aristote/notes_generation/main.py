import os
from typing import List, Optional

from transformers import PreTrainedTokenizerBase

from aristote.connectors.connectors import AbstractConnector
from aristote.dtos import TranscribedText
from aristote.notes_generation.notes_generator import NotesGenerator, NotesPromptsConfig
from aristote.preprocessing.preprocessing import (
    get_splits,
    get_tokenizer,
    load_file,
)
from aristote.reformulation.reformulation import create_reformulations

API_URL = "http://0.0.0.0:8000/generate"


def notes_generation(
    transcripts: List[TranscribedText],
    model_name: str,
    tokenizer: PreTrainedTokenizerBase,
    connector: AbstractConnector,
    prompts_config: NotesPromptsConfig,
    debug: bool = False,
    start_timestamp: str = None,
    end_timestamp: str = None,
    batch_size: Optional[int] = None,
) -> str:
    new_transcripts = get_splits(transcripts, tokenizer=tokenizer)
    if len(new_transcripts) > 20:
        new_transcripts = get_splits(transcripts, tokenizer=tokenizer, max_length=3000)

    print("Number of splits:", len(new_transcripts))

    if debug:
        print(new_transcripts)
        print("=======================================================")

    reformulations = create_reformulations(
        new_transcripts,
        model_name,
        tokenizer,
        connector,
        prompts_config.reformulation_prompt_path,
        batch_size=batch_size,
    )

    notes_generator = NotesGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        debug=debug,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        batch_size=batch_size,
    )
    notes = notes_generator.generate_notes(reformulations)
    return notes


def main(
    model_name: str,
    connector: AbstractConnector,
    transcript_path: str,
    prompts_config: NotesPromptsConfig,
    output_path: Optional[str] = None,
    debug: bool = False,
    start_timestamp: str = None,
    end_timestamp: str = None,
) -> None:
    tokenizer = get_tokenizer(model_name)
    transcripts = load_file(transcript_path)

    notes = notes_generation(
        transcripts,
        model_name,
        tokenizer,
        connector,
        prompts_config,
        debug,
        start_timestamp,
        end_timestamp,
    )

    if output_path is not None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(notes)
