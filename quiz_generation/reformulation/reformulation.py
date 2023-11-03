import re
from typing import List

from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector, Prompt
from quiz_generation.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)

PROMPT_REFORMULATION = (
    "Tu vas recevoir le transcript d'un cours."
    "Génère une description exhaustive du transcript suivant:\n"
    "[TRANSCRIPT]\n"
    "La description doit contenir tous les points essentiels du cours et "
    "pas de répétitions.\n"
    "Description:\n"
)


def create_reformulations(
    transcripts: List[str],
    model_name: str,
    tokenizer: AutoTokenizer,
    api_connector: APIConnector,
) -> List[str]:
    replaced_texts = [
        PROMPT_REFORMULATION.replace("[TRANSCRIPT]", transcript)
        for transcript in transcripts
    ]
    templated_transcripts = [
        get_templated_script(text, tokenizer) for text in replaced_texts
    ]
    reformulations = api_connector.multi_requests(
        prompts=[
            Prompt(
                text=templated_transcript,
                model_name=model_name,
                max_tokens=get_token_nb(templated_transcript, tokenizer),
                temperature=0.1,
            )
            for templated_transcript in templated_transcripts
        ],
        description="Generating reformulations",
    )
    reformulations = [
        reformulation.replace("\n\n", "\n") for reformulation in reformulations
    ]
    reformulations = [
        re.sub("([\n\\s]*[.?][\n\\s]*)^", "", reformulation)
        for reformulation in reformulations
    ]
    new_reformulations = []
    for reformulation in reformulations:
        new_reformulation = reformulation
        matches = list(re.finditer("([\n\\s]*[.?][\n\\s]*)", reformulation))
        if matches and matches[0].start() == 0:
            new_reformulation = new_reformulation[matches[0].end() :]
        new_reformulations.append(new_reformulation.strip())
    return new_reformulations
