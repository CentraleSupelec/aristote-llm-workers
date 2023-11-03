import re
import warnings
from typing import List

from transformers import AutoTokenizer


def get_token_nb(text: str, tokenizer: AutoTokenizer) -> int:
    token_nb = len(tokenizer.encode(text))
    if token_nb > 3000:
        warnings.warn(f"Text of size {token_nb} can be too long")
    return token_nb


def remove_newlines_before_lowercase(text: str) -> str:
    pattern = r"\n([a-z])"
    return re.sub(pattern, lambda match: " " + match.group(1), text)


def get_splits(
    transcripts: List[str], tokenizer: AutoTokenizer, max_length: int = 1000
) -> List[str]:
    """Get list of transcripts with length under max_length

    Args:
        transcripts (List[str]): list of transcripts
        max_length (int, optional): _description_. Defaults to 1000.

    Returns:
        List[str]: List of transcripts with length under max_length
    """
    new_transcripts = []
    new_transcript = ""
    for transcript in transcripts:
        longer_transcript = new_transcript + f"{transcript}\n"
        if get_token_nb(longer_transcript, tokenizer) > max_length:
            if len(new_transcript) > 0:
                new_transcripts.append(new_transcript.strip())
            new_transcript = f"{transcript}\n"
        else:
            new_transcript = longer_transcript
    new_transcripts.append(new_transcript.strip())

    new_transcripts = [
        remove_newlines_before_lowercase(transcript) for transcript in new_transcripts
    ]

    for i, transcript in enumerate(new_transcripts[:-1]):
        if not re.search(r"[.!?]$", transcript):
            last_text = re.split(r"[.!?]", transcript)[-1]
            new_transcripts[i] = new_transcripts[i][: -len(last_text)]
            new_transcripts[i + 1] = last_text + " " + new_transcripts[i + 1]

    if any(
        [
            get_token_nb(transcript, tokenizer) > max_length
            for transcript in new_transcripts
        ]
    ):
        warnings.warn("Some transcripts are still too long")

    return new_transcripts


def get_templated_script(text: str, tokenizer: AutoTokenizer) -> str:
    conversation = [{"role": "user", "content": text}]
    templated_transcript = str(
        tokenizer.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=True
        )
    )
    return templated_transcript
