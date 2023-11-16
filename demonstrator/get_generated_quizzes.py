import json
import os
from typing import Literal

import jsonlines
from unidecode import unidecode

transcript_name2path = {
    "mit_clustering": "data/mit_videos_transcripts/transcript_clustering.txt",
    "philosophy": "data/harvard_transcript/philosophy_lecture.txt",
    "cs_ri": "data/cs_videos_transcripts/transcript_ri.json",
    "cs_socio": "data/cs_videos_transcripts/transcript_sociologie.json",
}


def postprocess_answer(answer):
    if "." in answer:
        new_answer = answer.split(".")[0]
        return new_answer + "."
    return answer

def post_process(text, text_type):
    new_text = text.strip()
    splitted_text = new_text.split(":")
    if len(splitted_text) > 1:
        ablated_text = ":".join(splitted_text[1:]).strip()
        if splitted_text[0] == "":
            return ":".join(splitted_text[1:]).strip()
        else:
            first_text = unidecode(splitted_text[0].strip()).lower()
            if text_type == "question" and "quest" in first_text.lower():
                return ablated_text
            elif text_type == "answer" and (
                "reponse" in first_text.lower() or "answer" in first_text.lower()
            ):
                return postprocess_answer(ablated_text)
            elif text_type == "explanation" and (
                "explanation" in first_text.lower()
                or "explication" in first_text.lower()
                or ("reponse" in first_text.lower() and len(first_text) < 20)
            ):
                return postprocess_answer(ablated_text)
    if text_type == "answer":
        return postprocess_answer(new_text)
    return new_text


def get_generated_data(
    language_input: Literal["fr", "en"], model: str, transcript: str, order: bool
):
    quizzes = []

    if model == "bofenghuang/vigostral-7b-instruct":
        model_name = "vigostral"
    elif model == "HuggingFaceH4/zephyr-7b-beta":
        model_name = "zephyr"
    elif model == "gpt-4-1106-preview":
        model_name = "gpt-4"
    elif model == "gpt-3.5-turbo-1106":
        model_name = "gpt-35"
    else:
        raise ValueError("Model not recognized")

    metadata_filename = f"metadata_{model_name}_{language_input}_{transcript}.json"
    metadata_path = os.path.join(
        "experiments/2023-10-25_zero-shot-quiz-generation/",
        f"results/metadata/{metadata_filename}",
    )
    quizzes_filename = f"quizzes_{model_name}_{language_input}_{transcript}.jsonl"
    quizzes_path = os.path.join(
        "experiments/2023-10-25_zero-shot-quiz-generation/",
        f"results/quizzes/{quizzes_filename}",
    )
    with open(metadata_path) as file:
        metadata = json.load(file)
    with jsonlines.open(quizzes_path) as reader:
        for quiz in reader:
            new_quiz = quiz.copy()
            new_quiz["quiz"]["question"] = post_process(
                quiz["quiz"]["question"], "question"
            )
            new_quiz["quiz"]["answer"] = post_process(quiz["quiz"]["answer"], "answer")
            new_quiz["quiz"]["fake_answer_1"] = post_process(
                quiz["quiz"]["fake_answer_1"], "answer"
            )
            new_quiz["quiz"]["fake_answer_2"] = post_process(
                quiz["quiz"]["fake_answer_2"], "answer"
            )
            new_quiz["quiz"]["fake_answer_3"] = post_process(
                quiz["quiz"]["fake_answer_3"], "answer"
            )
            new_quiz["quiz"]["explanation"] = post_process(
                quiz["quiz"]["explanation"], "explanation"
            )
            quizzes.append(new_quiz)
    if order:
        quizzes = sorted(quizzes, key=lambda x: x["evaluation"]["score"], reverse=True)

    return metadata, quizzes
