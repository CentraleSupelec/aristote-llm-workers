import os
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import APIConnectorWithOpenAIFormat
from quiz_generation.metadata_generation.main import metadata_generation
from quiz_generation.metadata_generation.metadata_generator import (
    MetadataPromptsConfig,
)
from quiz_generation.quiz_generation.quiz_generator import (
    QuizGenerator,
    QuizPromptsConfig,
)
from server.dtos import (
    Choice,
    EnrichmentVersionMetadata,
    MultipleChoiceQuestion,
    QuizzesWrapper,
    TranscriptWrapper,
)

load_dotenv("envs/.env-server")

MODEL_NAME = os.environ.get("MODEL_NAME")
VLLM_API_URL = os.environ.get("VLLM_API_URL")
VLLM_CACHE_PATH = os.environ.get("VLLM_CACHE_PATH")
SUMMARY_PROMPT_PATH = os.environ.get("SUMMARY_PROMPT_PATH")
TITLE_PROMPT_PATH = os.environ.get("TITLE_PROMPT_PATH")
DESCRIPTION_PROMPT_PATH = os.environ.get("DESCRIPTION_PROMPT_PATH")
GENERATE_TOPICS_PROMPT_PATH = os.environ.get("GENERATE_TOPICS_PROMPT_PATH")
COMBINE_TOPICS_PROMPT_PATH = os.environ.get("COMBINE_TOPICS_PROMPT_PATH")
DISCIPLINE_PROMPT_PATH = os.environ.get("DISCIPLINE_PROMPT_PATH")
QUIZ_GENERATION_PROMPT_PATH = os.environ.get("QUIZ_GENERATION_PROMPT_PATH")

app = FastAPI(
    title="Quiz Generation API",
    version="0.0.1",
    description="Generate quizzes from texts",
)


@app.get("/")
def root():
    return {"message": "Welcome to the quiz generation API."}


@app.get("/health", tags=["health"])
def health():
    return True


def server_pipeline(
    language: str, disciplines: List[str], sentences: List[str]
) -> QuizzesWrapper:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    connector = APIConnectorWithOpenAIFormat(
        api_url=VLLM_API_URL,
        cache_path=VLLM_CACHE_PATH,
    )

    # TODO: Generate discipline
    metadata_prompt_config = MetadataPromptsConfig(
        summary_prompt_path=SUMMARY_PROMPT_PATH,
        title_prompt_path=TITLE_PROMPT_PATH,
        description_prompt_path=DESCRIPTION_PROMPT_PATH,
        generate_topics_prompt_path=GENERATE_TOPICS_PROMPT_PATH,
        combine_topics_prompt_path=COMBINE_TOPICS_PROMPT_PATH,
        discipline_prompt_path=DISCIPLINE_PROMPT_PATH,
    )
    metadata = metadata_generation(
        transcripts=sentences,
        language=language,
        model_name=MODEL_NAME,
        tokenizer=tokenizer,
        connector=connector,
        prompts_config=metadata_prompt_config,
        disciplines=disciplines,
    )

    # TODO: Generate Quizzes
    prompts_config = QuizPromptsConfig(
        quiz_generation_prompt=QUIZ_GENERATION_PROMPT_PATH,
    )
    quiz_generator = QuizGenerator(
        model_name=MODEL_NAME,
        tokenizer=tokenizer,
        api_connector=connector,
        language=language,
        prompts_config=prompts_config,
        chunks_path=None,
    )
    quizzes = quiz_generator.full_generation(sentences)
    formatted_quizzes = [
        MultipleChoiceQuestion(
            question=quiz.question,
            explanation=quiz.explanation,
            choices=[
                Choice(option_text=quiz.answer, correct_answer=True),
                Choice(option_text=quiz.fake_answer_1, correct_answer=False),
                Choice(option_text=quiz.fake_answer_2, correct_answer=False),
                Choice(option_text=quiz.fake_answer_3, correct_answer=False),
            ],
        )
        for quiz in quizzes
    ]

    # TODO: Generate evaluation

    return QuizzesWrapper(
        enrichment_version_metadata=EnrichmentVersionMetadata(
            title=metadata.title,
            description=metadata.description,
            topics=metadata.main_topics,
            discipline=metadata.discipline,
            media_type=metadata.media_type,
        ),
        multiple_choice_questions=formatted_quizzes,
    )


@app.post("/generate-quizzes", response_model=QuizzesWrapper)
def generate(transcript: TranscriptWrapper):
    disciplines = transcript.disciplines
    sentences = [sentence.text for sentence in transcript.transcript.sentences]
    return server_pipeline(transcript.transcript.language, disciplines, sentences)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
