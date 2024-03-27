import json
from typing import List, Optional

from transformers import PreTrainedTokenizerBase

from aristote.connectors.connectors import AbstractConnector
from aristote.dtos import MetaData, TranscribedText
from aristote.metadata_generation.metadata_generator import (
    MetadataGenerator,
    MetadataPromptsConfig,
)
from aristote.preprocessing.preprocessing import (
    get_splits,
    get_tokenizer,
    load_file,
)
from aristote.reformulation.reformulation import create_reformulations

API_URL = "http://0.0.0.0:8000/generate"


def metadata_generation(
    transcripts: List[TranscribedText],
    model_name: str,
    tokenizer: PreTrainedTokenizerBase,
    connector: AbstractConnector,
    prompts_config: MetadataPromptsConfig,
    debug: bool = False,
    disciplines: Optional[List[str]] = None,
) -> MetaData:
    new_transcripts = get_splits(transcripts, tokenizer=tokenizer)
    if len(new_transcripts) > 20:
        new_transcripts = get_splits(transcripts, tokenizer=tokenizer, max_length=3000)
    if len(new_transcripts) > 20:
        raise ValueError(f"Too many splits {len(new_transcripts)}")

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
    )

    metadata_generator = MetadataGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        debug=debug,
        disciplines=disciplines,
    )
    metadata = metadata_generator.generate_metadata(reformulations)
    return metadata


def main(
    model_name: str,
    connector: AbstractConnector,
    transcript_path: str,
    prompts_config: MetadataPromptsConfig,
    output_path: Optional[str] = None,
    debug: bool = False,
    disciplines: Optional[List[str]] = None,
) -> None:
    tokenizer = get_tokenizer(model_name)
    transcripts = load_file(transcript_path)

    metadata = metadata_generation(
        transcripts,
        model_name,
        tokenizer,
        connector,
        prompts_config,
        debug,
        disciplines,
    )

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(metadata.model_dump(mode="json"), file)
