import hashlib
import json
import re
import warnings
from typing import List

import click
import requests
from diskcache import Cache
from pydantic import BaseModel, constr
from tqdm import tqdm
from transformers import AutoTokenizer

cache = Cache(".cache2")

PROMPT_REFORMULATION = (
    "Tu vas recevoir un transcript d'un cours sur la recherche d'informations"
    "Génère une reformulation du transcript suivant:\n"
    "[TRANSCRIPT]\n"
    "La reformulation doit contenir tous les points essentiels et pas de répétitions.\n"
    "Reformulation:\n"
)

MODEL_NAME = "bofenghuang/vigostral-7b-chat"
tokenizer = AutoTokenizer.from_pretrained("bofenghuang/vigostral-7b-chat")


def get_cache_key(text, model_name):
    str_to_encode = f"{model_name}-{text}"
    return str(hashlib.sha256(str_to_encode.encode()).hexdigest())


def generate(
    text: str,
    max_tokens: int = 256,
    temperature: float = 0.5,
    stop: List[str] = None,
) -> str:
    cache_key = get_cache_key(text, MODEL_NAME)
    cached_text = cache.get(cache_key)
    if cached_text is not None:
        return cached_text
    else:
        res = requests.post(
            "http://0.0.0.0:8000/generate",
            json={
                "prompt": text,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop,
            },
            timeout=1000,
        ).json()["text"][0][len(text) :]
        cache.set(cache_key, res)
        return res


class MultipleAnswerQuiz(BaseModel):
    question: constr(min_length=10)
    answer: constr(min_length=1)
    fake_answer_1: constr(min_length=1)
    fake_answer_2: constr(min_length=1)
    fake_answer_3: constr(min_length=1)
    explanation: constr(min_length=10)


def generate_quiz(excerpt):
    # Generate question
    conv = [
        {
            "role": "user",
            "content": (
                "Tu es un assistant d'enseignement qui aide un professeur à créer un examen des "
                "connaissances pour ses élèves. Génère une question à propos de l'extrait suivant "
                "qui peut être répondue en une phrase:\n"
                f"{excerpt}\n"
                "Génère également la réponse à la question en une phrase."
                "La réponse doit être dans l'extrait."
                "Tu dois également fournir 3 fausses réponses en une phrase chacune."
                "Une des fausses réponses doit être évidemment fausse mais liée à l'extrait."
                "Les deux autres doivent être subtilement fausses."
                "Tu dois également fournir une explication pour la réponse et les fausses réponses.\n"
                "Voici la question et ces réponses:\n"
                "Question:\n"
            ),
        },
    ]
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    question = generate(text, max_tokens=256, stop=["?"])
    question += "?"
    conv += [
        {"role": "assistant", "content": question},
        {"role": "user", "content": "Réponse:"},
    ]
    # print(conv)
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    answer = generate(text, max_tokens=256, stop=["."])
    answer += "."
    conv += [
        {"role": "assistant", "content": answer},
        {"role": "user", "content": "Fausse Réponse 1:"},
    ]
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    fake_answer_1 = generate(text, max_tokens=256, stop=["."])
    fake_answer_1 += "."
    conv += [
        {"role": "assistant", "content": fake_answer_1},
        {"role": "user", "content": "Fausse Réponse 2:"},
    ]
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    fake_answer_2 = generate(text, max_tokens=256, stop=["."])
    fake_answer_2 += "."
    conv += [
        {"role": "assistant", "content": fake_answer_2},
        {"role": "user", "content": "Fausse Réponse 3:"},
    ]
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    fake_answer_3 = generate(text, max_tokens=256, stop=["."])
    fake_answer_3 += "."
    conv += [
        {"role": "assistant", "content": fake_answer_3},
        {"role": "user", "content": "Explication:"},
    ]
    text = tokenizer.apply_chat_template(conversation=conv, tokenize=False, add_generation_prompt=True)
    explanation = generate(
        text,
        max_tokens=800,
    )
    return MultipleAnswerQuiz(
        question=question,
        answer=answer,
        fake_answer_1=fake_answer_1,
        fake_answer_2=fake_answer_2,
        fake_answer_3=fake_answer_3,
        explanation=explanation,
    )


def get_token_nb(text: str):
    return len(tokenizer.encode(text))


def get_good_length_transcripts(transcripts: List[str], max_length: int = 1000):
    """Get list of transcripts with length under max_length

    Args:
        transcripts (List[str]): list of transcripts
        max_length (int, optional): _description_. Defaults to 1000.

    Returns:
        _type_: _description_
    """
    new_tanscripts = []
    new_transcript = ""
    for transcript in transcripts:
        longer_transcript = new_transcript + f"{transcript}\n"
        if get_token_nb(longer_transcript) > max_length:
            if len(new_transcript) > 0:
                new_tanscripts.append(new_transcript.strip())
            new_transcript = f"{transcript}\n"
        else:
            new_transcript = longer_transcript
    new_tanscripts.append(new_transcript.strip())
    if any([get_token_nb(transcript) > max_length for transcript in new_tanscripts]):
        warnings.warn("Some transcripts are still too long")

    return new_tanscripts


def replace_special_characters(text):
    # Define a regular expression pattern to match special UTF-8 characters
    pattern = r"\\u[0-9a-fA-F]{4}"

    # Use re.sub to replace matched patterns with their corresponding characters
    def replace(match):
        return chr(int(match.group(0)[2:], 16))

    result = re.sub(pattern, replace, text)
    return result


@click.command()
@click.option("--transcript_path", help="Transcript path to generate quiz from")
@click.option("--output_path", help="Path to generate output.")
def main(transcript_path, output_path):
    with open(transcript_path, "r") as f:
        transcripts = json.load(f)["transcripts"]

    new_transcripts = get_good_length_transcripts(transcripts)

    with open(output_path, "w") as file:
        for i, new_transcript in tqdm(enumerate(new_transcripts), total=len(new_transcripts)):
            file.write(f"# Transcript {i+1}\n\n")

            print("Generating reformulation...")
            initial_text = PROMPT_REFORMULATION.replace("[TRANSCRIPT]", new_transcript)

            file.write("## Prompt\n\n")
            file.write(f"```txt\n{initial_text}\n```\n\n")
            conversation = [
                {"role": "user", "content": initial_text},
            ]
            text = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
            reformulation = generate(
                text,
                max_tokens=get_token_nb(text),
            )
            reformulation = reformulation.replace("\n\n", "\n")
            file.write("## Reformulation\n\n")
            file.write(f"```txt\n{reformulation}\n```\n\n")

            print("Generating quiz...")
            quiz = generate_quiz(reformulation)
            quiz_json = quiz.model_dump(mode="json")
            quiz_str = json.dumps(quiz_json, indent=4)
            quiz_str = replace_special_characters(quiz_str)
            file.write("## Quiz\n\n")
            file.write(f"```txt\n{quiz_str}\n```\n\n")


if __name__ == "__main__":
    main()
