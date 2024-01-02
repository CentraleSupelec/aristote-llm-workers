import re
from typing import List, Literal

from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
)
from quiz_generation.preprocessing.preprocessing import (
    get_token_nb,
)

PROMPT_REFORMULATION_EN = (
    "You will receive the transcript of a course. "
    "Rewrite the following transcript without the noise of the transcription as if it "
    "was on a textbook:\n[TRANSCRIPT]\n"
    "The final text should contain all the essential information of the course "
    "and no repetitions.\n"
    "Text:\n"
)

PROMPT_REFORMULATION_FR = (
    "Tu vas recevoir le transcript d'un cours. "
    "Reformule le transcript suivant sans le bruit de la transcription comme si "
    "c'était dans un livre de cours:\n[TRANSCRIPT]\n"
    "La reformulation doit contenir tous les points essentiels du cours et "
    "pas de répétitions.\n"
    "Réponds en français.\n"
    "Texte:\n"
)


def create_reformulations(
    transcripts: List[str],
    model_name: str,
    tokenizer: AutoTokenizer,
    api_connector: AbstractConnector,
    language: Literal["en", "fr"],
) -> List[str]:
    if language == "en":
        base_prompt = PROMPT_REFORMULATION_EN
    elif language == "fr":
        base_prompt = PROMPT_REFORMULATION_FR
    else:
        raise ValueError("Language must be 'en' or 'fr'")

    replaced_texts = [
        base_prompt.replace("[TRANSCRIPT]", transcript) for transcript in transcripts
    ]
    # templated_transcripts = [
    #     get_templated_script(text, tokenizer) for text in replaced_texts
    # ]
    reformulations = api_connector.custom_multi_requests(
        prompts=[
            CustomPrompt(
                text=text,
                parameters=CustomPromptParameters(
                    model_name=model_name,
                    max_tokens=get_token_nb(text, tokenizer),
                    temperature=0.1,
                ),
            )
            for text in replaced_texts
        ],
        progress_desc="Generating reformulations",
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
