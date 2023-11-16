import json
from typing import Literal

from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector
from quiz_generation.metadata_generation.metadata_generator import (
    MetadataGenerator,
    MetadataPromptsConfig,
)
from quiz_generation.preprocessing.preprocessing import get_splits, load_file
from quiz_generation.reformulation.reformulation import create_reformulations

API_URL = "http://0.0.0.0:8000/generate"


def main(
    model_name: str,
    cache_path: str,
    transcript_path: str,
    language: Literal["en", "fr"],
    prompts_config: MetadataPromptsConfig,
    output_path: str,
) -> None:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    api_connector = APIConnector(API_URL, cache_path)

    transcripts = load_file(transcript_path)

    new_transcripts = get_splits(transcripts, tokenizer=tokenizer)

    reformulations = create_reformulations(
        new_transcripts, model_name, tokenizer, api_connector, language
    )

    metadata_generator = MetadataGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=api_connector,
        prompts_config=prompts_config,
    )
    metadata = metadata_generator.generate_metadata(reformulations)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(metadata.model_dump(mode="json"), file)
