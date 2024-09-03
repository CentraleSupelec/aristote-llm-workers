import base64
import json
import os
import sys
import uuid

import requests
from dotenv import load_dotenv
from requests.models import Response

sys.path.append("./")

from aristote.custom_exceptions import NotResponsiveModelError
from server.app import generate
from server.server_dtos import (
    Transcript,
    TranscriptWrapper,
)

load_dotenv(".env")

ARISTOTE_API_BASE_URL = os.environ["ARISTOTE_API_BASE_URL"]
ARISTOTE_API_CLIENT_ID = os.environ["ARISTOTE_API_CLIENT_ID"]
ARISTOTE_API_CLIENT_SECRET = os.environ["ARISTOTE_API_CLIENT_SECRET"]


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
                f"{ARISTOTE_API_CLIENT_ID}:{ARISTOTE_API_CLIENT_SECRET}".encode()
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
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/job/ai_enrichment/oldest?taskId={task_id}",
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
        media_types = json_response["mediaTypes"]
        disciplines = json_response["disciplines"]
        generate_metadata = json_response["generateMetadata"]
        generate_quiz = json_response["generateQuiz"]
        generate_notes = json_response["generateNotes"]
    else:
        print(f"Couldn't get a job. Error code : {job_response.status_code}")
        return

    print("Enrichment ID : ", enrichment_id)
    print("Disciplines : ", disciplines)
    print("Media types : ", media_types)

    try:
        enrichment_result = generate(
            transcript=TranscriptWrapper(
                enrichment_version_id=enrichment_version_id,
                transcript=Transcript(
                    original_file_name=transcript["originalFilename"],
                    language=(
                        transcript["language"]
                        if transcript
                        and "language" in transcript
                        and transcript["language"] is not None
                        and transcript["language"] != ""
                        else "fr"
                    ),
                    text=transcript["text"],
                    sentences=transcript["sentences"],
                ),
            ),
            disciplines=disciplines,
            media_types=media_types,
            generate_metadata=generate_metadata,
            generate_quiz=generate_quiz,
            generate_notes=generate_notes,
        )
    except NotResponsiveModelError as e:
        print(e)
        print(f"Aborting enrichment {enrichment_id}")
        return

    enrichment_result.task_id = task_id

    if generate_metadata:
        print(
            "Discipline : ", [enrichment_result.enrichment_version_metadata.discipline]
        )
        print(
            "Media type : ", [enrichment_result.enrichment_version_metadata.media_type]
        )

        if enrichment_result.enrichment_version_metadata.discipline not in disciplines:
            enrichment_result.enrichment_version_metadata.discipline = None
        if enrichment_result.enrichment_version_metadata.media_type not in media_types:
            enrichment_result.enrichment_version_metadata.media_type = None

    enrichment_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/v1/enrichments/{enrichment_id}/versions/{enrichment_version_id}/ai_enrichment",
        json=json.loads(enrichment_result.model_dump_json(by_alias=True)),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    if enrichment_response.status_code == 200:
        print("Enrichment successful !")
    else:
        print(f"Enrichment failed. Error code : {enrichment_response.status_code}")
        error_message = enrichment_response.json()
        if error_message:
            print(f"Error message : {error_message}")
        return


if __name__ == "__main__":
    aristote_worklow()
