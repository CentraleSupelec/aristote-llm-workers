import json
import re
from typing import List, Union

from nltk import sent_tokenize
from tiktoken import Encoding, encoding_for_model
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from quiz_generation.dtos.dtos import TranscribedText


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


def load_txt(path: str) -> List[TranscribedText]:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    lowercase_percentage = get_lowercase_percentage(re.split("\n{2,}", text))

    # Remove newlines before lowercase when there is enough lines starting with
    # uppercase. This makes the splits more coherent as they will start with
    # an uppercase.
    if lowercase_percentage < 0.7:
        text = remove_newlines_before_lowercase(text)
        texts = re.split("\n{3,}", text)
        texts = [re.sub("\n{2,}", " ", transcript) for transcript in texts]
    else:
        texts = re.split("\n{2,}", text)
        texts = [re.sub("\n{2,}", " ", transcript) for transcript in texts]

    transcripts = [
        TranscribedText(
            text=text,
        )
        for text in texts
    ]
    return transcripts


def load_json(path: str) -> List[TranscribedText]:
    with open(path, "r", encoding="utf-8") as file:
        texts: List[str] = json.load(file)["transcripts"]
    transcripts = [
        TranscribedText(
            text=text,
        )
        for text in texts
    ]
    return transcripts


def load_file(path: str) -> List[TranscribedText]:
    if path.endswith(".txt"):
        return load_txt(path)
    elif path.endswith(".json"):
        return load_json(path)
    else:
        raise ValueError("File format not supported")


def get_token_nb(
    text: str,
    tokenizer: Union[AutoTokenizer, Encoding],
    add_special_tokens: bool = True,
) -> int:
    token_nb = len(tokenizer.encode(text, add_special_tokens=add_special_tokens))
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
    transcripts: List[TranscribedText],
    tokenizer: AutoTokenizer,
    max_length: int = 1000,
) -> List[TranscribedText]:
    transcripts_to_process = []
    max_length_tenth = max_length // 10
    false_max_length = max_length - max_length_tenth
    for transcript in transcripts:
        start = transcript.start
        transcript_length = get_token_nb(
            transcript.text, tokenizer, add_special_tokens=False
        )
        if transcript.start is None or transcript.end is None:
            audio_length = None
        else:
            audio_length = transcript.end - transcript.start
        if transcript_length > false_max_length:
            sentences = sent_tokenize(transcript.text)
            for sentence in sentences:
                sentence_length = get_token_nb(
                    sentence, tokenizer, add_special_tokens=False
                )
                if sentence_length > false_max_length:
                    splitted_sentence = sentence.split()
                    for i, word in enumerate(splitted_sentence):
                        # if i != len(splitted_sentence) - 1:
                        #     real_word = word + " "
                        # else:
                        #     real_word = word
                        word_length = get_token_nb(
                            word, tokenizer, add_special_tokens=False
                        )
                        if transcript.start is None or transcript.end is None:
                            transcripts_to_process.append(
                                TranscribedText(text=word, start=None, end=None)
                            )
                        else:
                            end = start + (
                                word_length * audio_length / transcript_length
                            )
                            transcripts_to_process.append(
                                TranscribedText(text=word, start=start, end=end)
                            )
                            start = end
                else:
                    if transcript.start is None or transcript.end is None:
                        transcripts_to_process.append(
                            TranscribedText(text=sentence, start=None, end=None)
                        )
                    else:
                        end = start + (
                            sentence_length * audio_length / transcript_length
                        )
                        transcripts_to_process.append(
                            TranscribedText(text=sentence, start=start, end=end)
                        )
                        start = end
        else:
            transcripts_to_process.append(transcript)
    splits = []
    current_text = transcripts_to_process[0].text
    current_start = transcripts_to_process[0].start
    current_end = transcripts_to_process[0].end
    for next_transcript in transcripts_to_process[1:]:
        future_text = current_text + " " + next_transcript.text
        future_length = get_token_nb(future_text, tokenizer, add_special_tokens=False)
        if future_length >= false_max_length:
            splits.append(
                TranscribedText(
                    text=current_text,
                    start=current_start,
                    end=current_end,
                )
            )
            current_text = next_transcript.text
            current_start = next_transcript.start
            current_end = next_transcript.end
        else:
            current_text = future_text
            current_end = next_transcript.end
    if (
        len(splits) > 0
        and get_token_nb(current_text, tokenizer, add_special_tokens=False)
        < max_length_tenth
    ):
        splits[-1] = TranscribedText(
            text=splits[-1].text + " " + current_text,
            start=splits[-1].start,
            end=current_end,
        )
    else:
        splits.append(
            TranscribedText(
                text=current_text,
                start=current_start,
                end=current_end,
            )
        )
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
