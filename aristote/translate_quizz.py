import base64
import json
import os
import sys
import uuid

import requests
from dotenv import load_dotenv
from requests.models import Response

sys.path.append("./")

from server.app import translate
from server.server_dtos import (
    Choice,
    MultipleChoiceQuestion,
    Sentence,
    Transcript,
    TranslationInputtWrapper,
)

load_dotenv(".env")

ARISTOTE_API_BASE_URL = os.environ["ARISTOTE_API_BASE_URL"]
ARISTOTE_API_TRANSLATION_CLIENT_ID = os.environ["ARISTOTE_API_TRANSLATION_CLIENT_ID"]
ARISTOTE_API_TRANSLATION_CLIENT_SECRET = os.environ[
    "ARISTOTE_API_TRANSLATION_CLIENT_SECRET"
]


def enrichment_fail(
    enrichment_id: str,
    enrichment_version_id: str,
    task_id: str,
    token: str,
    failure_cause: str,
):
    failure_cause_trucated = (
        (failure_cause[:252] + "...") if len(failure_cause) > 255 else failure_cause
    )
    enrichment_failure_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/{enrichment_id}/versions/{enrichment_version_id}/ai_enrichment",
        json={
            "taskId": task_id,
            "status": "KO",
            "failureCause": failure_cause_trucated,
        },
        headers={"Authorization": "Bearer " + token},
    )

    if enrichment_failure_response.status_code == 200:
        print("Enrichemnt failure response sent")
    else:
        print("Couldn't send failure response")


def aristote_worklow():
    token_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/token",
        json={
            "grant_type": "client_credentials",
        },
        headers={
            "Authorization": "Basic "
            + base64.b64encode(
                f"{ARISTOTE_API_TRANSLATION_CLIENT_ID}:{ARISTOTE_API_TRANSLATION_CLIENT_SECRET}".encode()
            ).decode(),
        },
        timeout=1000,
    )

    if token_response.status_code == 200:
        token = token_response.json()["access_token"]
    else:
        print(f"Couldn't get token. Error code : {token_response.status_code}")
        return

    task_id = str(uuid.uuid4())

    job_response: Response = requests.get(
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/job/translation/oldest?taskId={task_id}",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        },
    )

    if job_response.status_code == 200:
        json_response = job_response.json()
        enrichment_id = json_response["enrichmentId"]
        enrichment_version_id = json_response["enrichmentVersionId"]
        transcript = json_response["transcript"]
        multiple_choice_questions = json_response["multipleChoiceQuestions"]
        print(json_response)
    else:
        print(f"Couldn't get a job. Error code : {job_response.status_code}")
        return

    quizz = translate(
        TranslationInputtWrapper(
            enrichment_version_metadata=json_response["enrichmentVersionMetadata"],
            transcript=Transcript(
                language=json_response["language"],
                text=transcript["text"],
                sentences=[
                    Sentence(
                        text=sentence["text"],
                        start=sentence["start"],
                        end=sentence["end"],
                    )
                    for sentence in transcript["sentences"]
                ],
            ),
            multiple_choice_questions=[
                MultipleChoiceQuestion(
                    id=multiple_choice_question["id"],
                    question=multiple_choice_question["question"],
                    explanation=multiple_choice_question["explanation"],
                    choices=[
                        Choice(
                            id=choice["id"],
                            option_text=choice["optionText"],
                            correct_answer=False,
                        )
                        for choice in multiple_choice_question["choices"]
                    ],
                )
                for multiple_choice_question in multiple_choice_questions
            ],
            from_language=json_response["language"],
            to_language=json_response["translateTo"],
        )
    )
    quizz.task_id = task_id

    enrichment_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/{enrichment_id}/versions/{enrichment_version_id}/translation",
        json=json.loads(quizz.model_dump_json(by_alias=True, exclude_none=True)),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    if enrichment_response.status_code == 200:
        print("Enrichment translation successful !")
    else:
        print(
            "Enrichment translation failed."
            + f"Error code : {enrichment_response.status_code}"
        )
        error_message = enrichment_response.json()
        if error_message:
            print(f"Error message : {error_message}")
        return


if __name__ == "__main__":
    aristote_worklow()
