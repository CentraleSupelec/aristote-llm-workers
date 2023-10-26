import json
import warnings
from typing import List

import click
import outlines.models as models
import outlines.text.generate as generate
import tiktoken
from pydantic import BaseModel, constr

PROMPT_REFORMULATION = (
    "Tu vas recevoir un transcript d'un cours sur l'Aprentissage par Renforcement"
    "Génère une reformulation du transcript suivant:\n"
    "[TRANSCRIPT]\n"
    "La reformulation doit contenir tous les points essentiels et pas de répétitions."
    "Reformulation:\n"
)

PROMPT_QUIZ = (
    "Génère une question à propos de l'extrait suivant qui peut être répondue en une phrase:\n"
    "[EXTRAIT]\n"
    "Génère également la réponse à la question en une phrase.\n"
    "La réponse doit être dans l'extrait.\n"
    "Tu dois également fournir 3 fausses réponses en une phrase chacune.\n"
    "Une des fausses réponses doit être évidemment fausse mais liée à l'extrait.\n"
    "Les deux autres doivent être subtilement fausses.\n"
    "Tu dois également fournir une explication pour la réponse et les fausses réponses.\n"
)
MODEL_NAME = "meta-llama/Llama-2-13b-chat-hf"


class MultipleAnswerQuiz(BaseModel):
    question: constr(min_length=10)
    answer: constr(min_length=1)
    fake_answer_1: constr(min_length=1)
    fake_answer_2: constr(min_length=1)
    fake_answer_3: constr(min_length=1)
    explanation: constr(min_length=10)


class Reformulation(BaseModel):
    reformulation: constr(min_length=1)


def generate_reformulation(transcript, model):
    generator = generate.json(model, Reformulation, max_tokens=100)
    sequence = generator(PROMPT_REFORMULATION.replace("[TRANSCRIPT]", transcript))
    return sequence.reformulation


def generate_quiz(excerpt, model):
    generator = generate.json(model, MultipleAnswerQuiz, max_tokens=100)
    quiz = generator(PROMPT_QUIZ.replace("[EXTRAIT]", excerpt))
    return quiz


def get_good_length_transcripts(transcripts: List[str], max_length: int = 1000):
    """Get list of transcripts with length under max_length

    Args:
        transcripts (List[str]): list of transcripts
        max_length (int, optional): _description_. Defaults to 1000.

    Returns:
        _type_: _description_
    """
    encoder = tiktoken.encoding_for_model(MODEL_NAME)
    new_tanscripts = []
    new_transcript = ""
    for transcript in transcripts:
        longer_transcript = new_transcript + f"{transcript}\n"
        if len(encoder.encode(longer_transcript)) > max_length:
            if len(new_transcript) > 0:
                new_tanscripts.append(new_transcript.strip())
            new_transcript = f"{transcript}\n"
        else:
            new_transcript = longer_transcript
    new_tanscripts.append(new_transcript.strip())
    if any([len(encoder.encode(transcript)) > max_length for transcript in new_tanscripts]):
        warnings.warn("Some transcripts are still too long")

    return new_tanscripts


@click.command()
@click.option("--transcript_path", help="Transcript path to generate quiz from")
def main(transcript_path):
    with open(transcript_path, "r") as f:
        transcripts = json.load(f)["transcripts"]

    _ = get_good_length_transcripts(transcripts)[0]
    _ = models.transformers(MODEL_NAME)


if __name__ == "__main__":
    main()
