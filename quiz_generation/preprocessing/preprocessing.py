import json
import re
from typing import List, Union

from nltk import sent_tokenize
from tiktoken import Encoding, encoding_for_model
from transformers import AutoTokenizer, PreTrainedTokenizerBase


def get_tokenizer(model_name: str) -> Union[PreTrainedTokenizerBase, Encoding]:
    if "gpt-4" in model_name or "gpt-3.5" in model_name:
        return encoding_for_model(model_name)
    else:
        return AutoTokenizer.from_pretrained(model_name)


def get_lowercase_percentage(transcripts: List[str]) -> float:
    """Get percentage of lowercase characters in transcripts

    Args:
        transcripts (List[str]): List of transcripts

    Returns:
        float: Percentage of lowercase characters in transcripts
    """
    lowercase_nb = 0
    total_nb = 0
    for transcript in transcripts:
        if len(transcript) > 0 and transcript[0].islower():
            lowercase_nb += 1
        total_nb += 1
    return lowercase_nb / total_nb


def remove_newlines_before_lowercase(text: str) -> str:
    pattern = r"\n{1,}([a-z])"
    return re.sub(pattern, lambda match: " " + match.group(1), text)


def load_txt(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    lowercase_percentage = get_lowercase_percentage(re.split("\n{2,}", text))

    # Remove newlines before lowercase when there is enough lines starting with
    # uppercase. This makes the splits more coherent as they will start with
    # an uppercase.
    if lowercase_percentage < 0.7:
        text = remove_newlines_before_lowercase(text)
        transcripts = re.split("\n{3,}", text)
        transcripts = [re.sub("\n{2,}", " ", transcript) for transcript in transcripts]
    else:
        transcripts = re.split("\n{2,}", text)
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
    transcripts: List[str],
    tokenizer: AutoTokenizer,
    max_length: int = 1000,
):
    transcripts_to_process = []
    max_length_tenth = max_length // 10
    false_max_length = max_length - max_length_tenth
    for transcript in transcripts:
        transcript_length = get_token_nb(transcript, tokenizer)
        if transcript_length > false_max_length:
            sentences = sent_tokenize(transcript)
            for sentence in sentences:
                sentence_length = get_token_nb(sentence, tokenizer)
                if sentence_length > false_max_length:
                    for word in sentence.split():
                        transcripts_to_process.append(word)
                else:
                    transcripts_to_process.append(sentence)
        else:
            transcripts_to_process.append(transcript)
    splits = []
    current_transcript = transcripts_to_process[0]
    for next_transcript in transcripts_to_process[1:]:
        future_transcript = current_transcript + " " + next_transcript
        future_length = get_token_nb(future_transcript, tokenizer)
        if future_length > false_max_length:
            splits.append(current_transcript)
            current_transcript = next_transcript
        else:
            current_transcript = future_transcript
    if (
        len(splits) > 0
        and get_token_nb(current_transcript, tokenizer) < max_length_tenth
    ):
        splits[-1] += " " + current_transcript
    else:
        splits.append(current_transcript)
    return splits


def get_templated_script(text: str, tokenizer: AutoTokenizer) -> str:
    templated_transcript = text
    # TODO Renvoyer string ou conversation ?

    # if isinstance(tokenizer, Encoding):
    #     templated_transcript = text
    # else:
    #     conversation = [{"role": "user", "content": text}]
    #     templated_transcript = str(
    #         tokenizer.apply_chat_template(
    #             conversation, tokenize=False, add_generation_prompt=True
    #         )
    #     )
    return templated_transcript
