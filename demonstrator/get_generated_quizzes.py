import json
import os
from typing import Literal

import jsonlines

transcript_name2path = {
    "mit_clustering": "data/mit_videos_transcripts/transcript_clustering.txt",
    "philosophy": "data/harvard_transcript/philosophy_lecture.txt",
    "cs_ri": "data/cs_videos_transcripts/transcript_ri.json",
    "cs_socio": "data/cs_videos_transcripts/transcript_sociologie.json",
}


def get_generated_data(
    language_input: Literal["fr", "en"], model: str, transcript: str
):
    quizzes = []

    if model == "bofenghuang/vigostral-7b-instruct":
        model_name = "vigostral"
    elif model == "HuggingFaceH4/zephyr-7b-beta":
        model_name = "zephyr"
    elif model in ["gpt-35", "gpt-4"]:
        model_name = model
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
            quizzes.append(quiz)

    return metadata, quizzes
