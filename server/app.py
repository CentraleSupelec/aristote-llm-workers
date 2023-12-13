from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import APIConnector
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

# LANGUAGE = os.environ.get("LANGUAGE")
# HF_TOKEN = os.environ.get("HF_KEY")
# MODEL_PATH = os.environ.get("MODEL_PATH")
# PRETRAINED_MODEL = os.environ.get("PRETRAINED_MODEL")
# OPENAI_KEY = os.environ.get("OPENAI_KEY")
MODEL_NAME = "teknium/OpenHermes-2.5-Mistral-7B"
VLLM_API_URL = "http://localhost:8000/generate"
VLLM_CACHE_PATH = ".llm_cache"
SUMMARY_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/summary_prompt.txt"
)
TITLE_PROMPT_PATH = "quiz_generation/quiz_generation/prompts/zephyr/title_prompt.txt"
DESCRIPTION_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/description_prompt.txt"
)
GENERATE_TOPICS_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/generate_topics_prompt.txt"
)
COMBINE_TOPICS_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/combine_topics_prompt.txt"
)
DISCIPLINE_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/discipline_prompt.txt"
)
MEDIA_TYPE_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/media_type_prompt.txt"
)
QUIZ_GENERATION_PROMPT_PATH = (
    "quiz_generation/quiz_generation/prompts/zephyr/quiz_generation_prompt.txt"
)

app = FastAPI(
    title="Quiz Generation API",
    version="0.0.1",
    description="Generate quizzes from texts",
)


@app.get("/")
def root():
    return {"message": "Welcome to the sentiment analyser api."}


@app.get("/health", tags=["health"])
def health():
    return True


def server_pipeline(
    language: str, disciplines: List[str], sentences: List[str]
) -> QuizzesWrapper:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    connector = APIConnector(
        api_url=VLLM_API_URL,
        cache_path=VLLM_CACHE_PATH,
    )

    # TODO: Generate metadata
    metadata_prompt_config = MetadataPromptsConfig(
        summary_prompt_path=SUMMARY_PROMPT_PATH,
        title_prompt_path=TITLE_PROMPT_PATH,
        description_prompt_path=DESCRIPTION_PROMPT_PATH,
        generate_topics_prompt_path=GENERATE_TOPICS_PROMPT_PATH,
        combine_topics_prompt_path=COMBINE_TOPICS_PROMPT_PATH,
        discipline_prompt_path=DISCIPLINE_PROMPT_PATH,
        media_type_prompt_path=MEDIA_TYPE_PROMPT_PATH,
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
                Choice(optionText=quiz.answer, correctAnswer=True),
                Choice(optionText=quiz.fake_answer_1, correctAnswer=False),
                Choice(optionText=quiz.fake_answer_2, correctAnswer=False),
                Choice(optionText=quiz.fake_answer_3, correctAnswer=False),
            ],
        )
        for quiz in quizzes
    ]
    # TODO: Generate evaluation

    return QuizzesWrapper(
        enrichmentVersionMetadata=EnrichmentVersionMetadata(
            title=metadata.title,
            description=metadata.description,
            topics=metadata.main_topics,
            discipline=metadata.discipline,
            mediaType=metadata.media_type,
        ),
        multipleChoiceQuestions=formatted_quizzes,
    )


@app.post("/generate-quizzes", response_model=QuizzesWrapper)
def generate(transcript: TranscriptWrapper):
    disciplines = transcript.disciplines
    sentences = [sentence.text for sentence in transcript.transcript.sentences]
    print(sentences)
    return server_pipeline(transcript.transcript.language, disciplines, sentences)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
