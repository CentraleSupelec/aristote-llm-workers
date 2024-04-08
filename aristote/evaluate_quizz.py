import base64
import json
import os
import sys
import uuid

import requests
from dotenv import load_dotenv
from requests.models import Response

sys.path.append("./")

from server.app import evaluate_quizzes
from server.server_dtos import EnrichmentVersionMetadata, QuizzesWrapper

load_dotenv(".env")

ARISTOTE_API_BASE_URL = os.environ["ARISTOTE_API_BASE_URL"]
ARISTOTE_API_EVALUATION_CLIENT_ID = os.environ["ARISTOTE_API_EVALUATION_CLIENT_ID"]
ARISTOTE_API_EVALUATION_CLIENT_SECRET = os.environ[
    "ARISTOTE_API_EVALUATION_CLIENT_SECRET"
]
EVALUATOR = os.environ["EVALUATOR"]


def aristote_worklow():
    token_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/token",
        json={
            "grant_type": "client_credentials",
        },
        headers={
            "Authorization": "Basic "
            + base64.b64encode(
                f"{ARISTOTE_API_EVALUATION_CLIENT_ID}:{ARISTOTE_API_EVALUATION_CLIENT_SECRET}".encode()
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
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/job/ai_evaluation/oldest?taskId={task_id}&evaluator={EVALUATOR}",
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
        enrichment_version_metadata = json_response["enrichmentVersionMetadata"]
    else:
        print(f"Couldn't get a job. Error code : {job_response.status_code}")
        return

    evaluations_wrapper = evaluate_quizzes(
        quizzes=QuizzesWrapper(
            multiple_choice_questions=multiple_choice_questions,
            enrichment_version_metadata=EnrichmentVersionMetadata(
                title=enrichment_version_metadata["title"],
                description=enrichment_version_metadata["description"],
                topics=enrichment_version_metadata["topics"],
            ),
        ),
        language=transcript["language"],
    )

    evaluations_wrapper.task_id = task_id
    evaluations_wrapper_camelcased = json.loads(
        evaluations_wrapper.model_dump_json(by_alias=True)
    )

    for evaluation in evaluations_wrapper_camelcased["evaluations"]:
        evaluation.pop("quiz", None)
        evaluation_copy = evaluation["evaluation"]
        evaluation_copy.pop("score", None)
        evaluation["evaluation"] = json.dumps(evaluation_copy)

    evaluation_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/{enrichment_id}/versions/{enrichment_version_id}/ai_evaluation",
        json=evaluations_wrapper_camelcased,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    if evaluation_response.status_code == 200:
        print("Evaluation successful !")
    else:
        print(f"Evaluation failed. Error code : {evaluation_response.status_code}")
        error_message = evaluation_response.json()
        if error_message:
            print(f"Error message : {error_message}")
        return


if __name__ == "__main__":
    aristote_worklow()
