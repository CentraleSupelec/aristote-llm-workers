import json

import click
import configue
from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector
from quiz_generation.metadata_generation.metadata_generator import MetadataGenerator
from quiz_generation.preprocessing.preprocessing import get_splits
from quiz_generation.reformulation.reformulation import create_reformulations

API_URL = "http://0.0.0.0:8000/generate"


@click.command()
@click.option("--config_path", type=str, help="Path to the configuration file.")
def main(config_path: str) -> None:
    config = configue.load(config_path)
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    api_connector = APIConnector(API_URL, config.cache_path)

    with open(config.transcript_path, "r", encoding="utf-8") as f:
        transcripts = json.load(f)["transcripts"]

    new_transcripts = get_splits(transcripts, tokenizer=tokenizer)

    reformulations = create_reformulations(
        new_transcripts, config.model_name, tokenizer, api_connector
    )

    metadata_generator = MetadataGenerator(
        model_name=config.model_name,
        tokenizer=tokenizer,
        api_connector=api_connector,
        prompts_config=config.prompts_config,
    )
    metadata = metadata_generator.generate_metadata(reformulations)

    with open(config.output_path, "w", encoding="utf-8") as file:
        json.dump(metadata.model_dump(mode="json"), file)


if __name__ == "__main__":
    main()
