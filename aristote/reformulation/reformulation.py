import re
from typing import List

from transformers import AutoTokenizer

from aristote.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
)
from aristote.dtos.dtos import Reformulation, TranscribedText
from aristote.preprocessing.preprocessing import (
    get_token_nb,
)


def create_reformulations(
    transcripts: List[TranscribedText],
    model_name: str,
    tokenizer: AutoTokenizer,
    api_connector: AbstractConnector,
    prompt_path: str,
    batch_size: int,
) -> List[Reformulation]:
    with open(prompt_path, "r", encoding="utf-8") as file:
        base_prompt = file.read()

    if "[TRANSCRIPT]" not in base_prompt:
        raise ValueError("Prompt does not contain [TRANSCRIPT]")

    replaced_texts = [
        base_prompt.replace("[TRANSCRIPT]", transcript.text)
        for transcript in transcripts
    ]
    reformulation_texts = api_connector.custom_multi_requests(
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
        progress_desc="Generating reformulation texts",
        batch_size=batch_size,
    )
    reformulation_texts = [
        reformulation.replace("\n\n", "\n") for reformulation in reformulation_texts
    ]
    reformulation_texts = [
        re.sub("([\n\\s]*[.?][\n\\s]*)^", "", reformulation)
        for reformulation in reformulation_texts
    ]
    new_reformulation_texts = []
    for reformulation in reformulation_texts:
        new_reformulation = reformulation
        matches = list(re.finditer("([\n\\s]*[.?][\n\\s]*)", reformulation))
        if matches and matches[0].start() == 0:
            new_reformulation = new_reformulation[matches[0].end() :]
        new_reformulation_texts.append(new_reformulation.strip())

    reformulations = [
        Reformulation(
            text=text,
            start=transcript.start,
            end=transcript.end,
        )
        for text, transcript in zip(new_reformulation_texts, transcripts)
    ]
    return reformulations
