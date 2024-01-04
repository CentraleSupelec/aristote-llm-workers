import json
from typing import Dict, Literal, Optional

import jsonlines
from unidecode import unidecode

with open("demonstrator/transcript_name2path.json", "r") as file:
    transcript_name2path = json.load(file)


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
            elif text_type == "title" and "title" in first_text.lower():
                return ablated_text
            elif text_type == "description" and "description" in first_text.lower():
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
    language_input: Literal["fr", "en"],
    model: str,
    transcript: str,
    order: bool,
    filters: Optional[Dict[str, bool]] = None,
):
    quizzes = []

    if model == "bofenghuang/vigostral-7b-instruct":
        model_name = "vigostral"
    elif model == "HuggingFaceH4/zephyr-7b-beta":
        model_name = "zephyr"
    elif model == "teknium/OpenHermes-2.5-Mistral-7B":
        model_name = "hermes"
    elif model == "gpt-4-1106-preview":
        model_name = "gpt4"
    elif model == "gpt-3.5-turbo-1106":
        model_name = "gpt-35"
    else:
        raise ValueError("Model not recognized")

    chunks_path = transcript_name2path[transcript]["chunks_path"].replace(
        "zephyr", model_name
    )
    metadata_path = transcript_name2path[transcript]["metadata_path"].replace(
        "zephyr", model_name
    )
    quizzes_path = transcript_name2path[transcript]["quizzes_path"].replace(
        "zephyr", model_name
    )

    with jsonlines.open(chunks_path) as reader:
        chunks = list(reader)

    with open(metadata_path, "r") as file:
        metadata = json.load(file)
        metadata["title"] = post_process(metadata["title"], "title")
        metadata["description"] = post_process(metadata["description"], "description")

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
    if filters is not None:
        kept_indexes = []
        kept_quizzes = []
        for i, quiz in enumerate(quizzes):
            if (
                (
                    not filters["is_related"]
                    or (filters["is_related"] and quiz["evaluation"]["is_related"])
                )
                and (
                    not filters["is_self_contained"]
                    or (
                        filters["is_self_contained"]
                        and quiz["evaluation"]["is_self_contained"]
                    )
                )
                and (
                    not filters["is_question"]
                    or (filters["is_question"] and quiz["evaluation"]["is_question"])
                )
                and (
                    not filters["language_is_clear"]
                    or (
                        filters["language_is_clear"]
                        and quiz["evaluation"]["language_is_clear"]
                    )
                )
                and (
                    not filters["answers_are_all_different"]
                    or (
                        filters["answers_are_all_different"]
                        and quiz["evaluation"]["answers_are_all_different"]
                    )
                )
                and (
                    not filters["fake_answers_are_not_obvious"]
                    or (
                        filters["fake_answers_are_not_obvious"]
                        and quiz["evaluation"]["fake_answers_are_not_obvious"]
                    )
                )
                and (
                    not filters["answers_are_related"]
                    or (
                        filters["answers_are_related"]
                        and quiz["evaluation"]["answers_are_related"]
                    )
                )
                and (
                    not filters["quiz_about_concept"]
                    or (
                        filters["quiz_about_concept"]
                        and quiz["evaluation"]["quiz_about_concept"]
                    )
                )
            ):
                kept_indexes.append(i)
                kept_quizzes.append(quiz)
    else:
        kept_indexes = list(range(len(quizzes)))
        kept_quizzes = quizzes
    if order:
        ordered_quizzes = sorted(
            list(enumerate(kept_quizzes)),
            key=lambda x: x[1]["evaluation"]["score"],
            reverse=True,
        )

        kept_quizzes = [quiz[1] for quiz in ordered_quizzes]
        kept_chunks = [chunks[kept_indexes[quiz[0]]] for quiz in ordered_quizzes]
    else:
        kept_chunks = [chunks[kept_indexes[i]] for i in range(len(kept_indexes))]

    return kept_chunks, metadata, kept_quizzes
