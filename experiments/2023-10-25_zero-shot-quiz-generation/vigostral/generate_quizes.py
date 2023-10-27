import json
import warnings
from typing import List

import click
import guidance
import tiktoken
from pydantic import BaseModel, constr
from tqdm import tqdm
import requests
from transformers import AutoTokenizer
from typing import Dict, List
from diskcache import Cache
import hashlib

cache = Cache(".cache")

PROMPT_REFORMULATION = (
    "Tu vas recevoir un transcript d'un cours sur la recherche d'informations"
    "Génère une reformulation du transcript suivant:\n"
    "[TRANSCRIPT]\n"
    "La reformulation doit contenir tous les points essentiels et pas de répétitions.\n"
    "Reformulation:\n"
)

QUIZ_PROMPT = """
{{#system~}}
Tu es un assistant d'enseignement qui aide un professeur à créer un examen des connaissances pour ses élèves.
{{~/system}}
{{#user~}}
Génère une question à propos de l'extrait suivant qui peut être répondue en une phrase:
[EXTRACT]
Génère également la réponse à la question en une phrase.
La réponse doit être dans l'extrait.
Tu dois également fournir 3 fausses réponses en une phrase chacune.
Une des fausses réponses doit être évidemment fausse mais liée à l'extrait.
Les deux autres doivent être subtilement fausses.
Tu dois également fournir une explication pour la réponse et les fausses réponses.
Voici la question et ces réponses:
Question:
{{~/user}}
{{#assistant~}}
{{gen 'question' stop='?' temperature=0.7}}
{{~/assistant}}
{{#user~}}
Réponse:
{{~/user}}
{{#assistant~}}
{{gen 'answer' stop='.' temperature=0.2}}
{{~/assistant}}
{{#user~}}
Fausse Réponse 1:
{{~/user}}
{{#assistant~}}
{{gen 'fake_answer_1' stop='.' temperature=0.2}}
{{~/assistant}}
{{#user~}}
Fausse Réponse 2:
{{~/user}}
{{#assistant~}}
{{gen 'fake_answer_2' stop='.' temperature=0.2}}
{{~/assistant}}
{{#user~}}
Fausse Réponse 3:
{{~/user}}
{{#assistant~}}
{{gen 'fake_answer_3' stop='.' temperature=0.2}}
{{~/assistant}}
{{#user~}}
Explication:
{{~/user}}
{{#assistant~}}
{{gen 'explanation' temperature=0.5}}
{{~/assistant}}
"""

MODEL_NAME = "bofenghuang/vigostral-7b-chat"
tokenizer = AutoTokenizer.from_pretrained("bofenghuang/vigostral-7b-chat")


def get_cache_key(text, model_name):
    str_to_encode = f"{model_name}-{text}"
    return str(hashlib.sha256(str_to_encode.encode()).hexdigest())

def generate(text: str, max_length: int = 256, do_sample: bool = False, temperature: float = 0.5) -> str:
    cache_key = get_cache_key(text, MODEL_NAME)
    cached_text = cache.get(cache_key)
    if cached_text is not None:
        return cached_text
    else:
        res = requests.post(
            "http://0.0.0.0:8000/generate",
            json={
                "text": text,
                "parameters": {
                    "max_new_tokens": max_length,
                    "do_sample": do_sample,
                    "temperature": temperature,
                }
            },
            timeout=1000,
        ).json()["generation"]
        cache.set(cache_key, res)
        return res


# class MultipleAnswerQuiz(BaseModel):
#     question: constr(min_length=10)
#     answer: constr(min_length=1)
#     fake_answer_1: constr(min_length=1)
#     fake_answer_2: constr(min_length=1)
#     fake_answer_3: constr(min_length=1)
#     explanation: constr(min_length=10)


# def generate_quiz(excerpt, model):
#     quiz_prompt = QUIZ_PROMPT.replace("[EXTRACT]", excerpt)
#     quiz_prompt = quiz_prompt.replace("[TEMPERATURE]", str(0))
#     print(quiz_prompt)
#     quiz_guidance = guidance(quiz_prompt)
#     quiz = quiz_guidance(llm=model)
#     return quiz

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


@click.command()
@click.option("--transcript_path", help="Transcript path to generate quiz from")
@click.option("--output_path", help="Path to generate output.")
def main(transcript_path, output_path):

    with open(transcript_path, "r") as f:
        transcripts = json.load(f)["transcripts"]

    new_transcripts = get_good_length_transcripts(transcripts)[:1]

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
            text = tokenizer.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
            reformulation = generate(
                text,
                max_length=get_token_nb(text),
            )
            reformulation = reformulation.replace("\n\n", "\n")
            file.write("## Reformulation\n\n")
            file.write(f"```txt\n{reformulation}\n```\n\n")

            # print("Generating quiz...")
            # guidance_model = guidance.llms.OpenAI(model_name)
            # quiz = generate_quiz(reformulation, guidance_model)
            # file.write("## Quiz\n\n")
            # file.write(f"```txt\n{quiz}\n```\n\n")


if __name__ == "__main__":
    main()
