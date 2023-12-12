import json
from typing import Literal

from quiz_generation.connectors.connectors import AbstractConnector
from quiz_generation.metadata_generation.metadata_generator import (
    MetadataGenerator,
    MetadataPromptsConfig,
)
from quiz_generation.preprocessing.preprocessing import (
    get_splits,
    get_tokenizer,
    load_file,
)
from quiz_generation.reformulation.reformulation import create_reformulations

API_URL = "http://0.0.0.0:8000/generate"


def main(
    model_name: str,
    connector: AbstractConnector,
    transcript_path: str,
    language: Literal["en", "fr"],
    prompts_config: MetadataPromptsConfig,
    output_path: str,
    debug: bool = False,
) -> None:
    tokenizer = get_tokenizer(model_name)

    transcripts = load_file(transcript_path)

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
        new_transcripts, model_name, tokenizer, connector, language
    )

    metadata_generator = MetadataGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        debug=debug,
    )
    metadata = metadata_generator.generate_metadata(reformulations)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(metadata.model_dump(mode="json"), file)
