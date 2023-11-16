import json
import re
import warnings
from typing import List, Union

from nltk import sent_tokenize
from tiktoken import Encoding, encoding_for_model
from transformers import AutoTokenizer


def get_tokenizer(model_name: str) -> Union[AutoTokenizer, Encoding]:
    if "gpt-4" in model_name or "gpt-3.5" in model_name:
        return encoding_for_model(model_name)
    else:
        return AutoTokenizer.from_pretrained(model_name)


def load_txt(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    text = remove_newlines_before_lowercase(text)
    transcripts = re.split("\n{3,}", text)
    transcripts = [re.sub("\n{2,}", " ", transcript) for transcript in transcripts]
    return transcripts


def load_json(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        transcripts: List[str] = json.load(file)["transcripts"]
    return transcripts


def load_file(path: str) -> List[str]:
    if path.endswith(".txt"):
        return load_txt(path)
    elif path.endswith(".json"):
        return load_json(path)
    else:
        raise ValueError("File format not supported")


def get_token_nb(text: str, tokenizer: Union[AutoTokenizer, Encoding]) -> int:
    token_nb = len(tokenizer.encode(text))
    return token_nb


def remove_newlines_before_lowercase(text: str) -> str:
    pattern = r"\n{1,}([a-z])"
    return re.sub(pattern, lambda match: " " + match.group(1), text)


def divide_transcript(
    transcript: str, tokenizer: AutoTokenizer, max_length: int = 1000
) -> List[str]:
    sentences = sent_tokenize(transcript)
    new_transcripts = []
    new_transcript = ""
    for sentence in sentences:
        longer_transcript = new_transcript + f"{sentence} "
        if get_token_nb(longer_transcript, tokenizer) > max_length:
            if len(new_transcript) > 0:
                new_transcripts.append(new_transcript.strip())
            new_transcript = f"{sentence} "
        else:
            new_transcript = longer_transcript
    return new_transcripts


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

    splitted_transcripts = []
    for transcript in new_transcripts:
        if get_token_nb(transcript, tokenizer) > max_length:
            splitted_transcripts.extend(
                divide_transcript(transcript, tokenizer, max_length)
            )
        else:
            splitted_transcripts.append(transcript)

    for transcript in splitted_transcripts:
        token_nb = get_token_nb(transcript, tokenizer)
        if token_nb > max_length:
            warnings.warn(f"A transcript of size {token_nb} are still too long")
    return splitted_transcripts


def get_templated_script(text: str, tokenizer: AutoTokenizer) -> str:
    conversation = [{"role": "user", "content": text}]
    if isinstance(tokenizer, Encoding):
        templated_transcript = text
    else:
        templated_transcript = str(
            tokenizer.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
        )
    return templated_transcript


# if __name__ == "__main__":
#     text = load_txt("data/mit_videos_transcripts/transcript_clustering.txt")
#     print(text)
