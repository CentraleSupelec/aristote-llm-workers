import os
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import (
    APIConnectorWithOpenAIFormat,
    CustomOpenAIConnector,
)
from quiz_generation.evaluation.evaluator import EvaluationPromptsConfig, Evaluator
from quiz_generation.metadata_generation.main import metadata_generation
from quiz_generation.metadata_generation.metadata_generator import (
    MetaData,
    MetadataPromptsConfig,
)
from quiz_generation.quiz_generation.quiz_generator import (
    MultipleAnswerQuiz,
    QuizGenerator,
    QuizPromptsConfig,
)
from server.dtos import (
    Choice,
    EnrichmentVersionMetadata,
    EvaluationsWrapper,
    MultipleChoiceQuestion,
    QuizzesWrapper,
    TranscriptWrapper,
)

load_dotenv(".env")

MODEL_NAME = os.environ.get("MODEL_NAME")
VLLM_API_URL = os.environ.get("VLLM_API_URL")
VLLM_CACHE_PATH = os.environ.get("VLLM_CACHE_PATH")

SUMMARY_PROMPT_PATH = os.environ.get("SUMMARY_PROMPT_PATH")
TITLE_PROMPT_PATH = os.environ.get("TITLE_PROMPT_PATH")
DESCRIPTION_PROMPT_PATH = os.environ.get("DESCRIPTION_PROMPT_PATH")
GENERATE_TOPICS_PROMPT_PATH = os.environ.get("GENERATE_TOPICS_PROMPT_PATH")
DISCIPLINE_PROMPT_PATH = os.environ.get("DISCIPLINE_PROMPT_PATH")

QUIZ_GENERATION_PROMPT_PATH = os.environ.get("QUIZ_GENERATION_PROMPT_PATH")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID")
OPEN_AI_CACHE_PATH = os.environ.get("OPENAI_ORG_ID")
EVALUATION_MODEL_NAME = os.environ.get("EVALUATION_MODEL_NAME")

IS_RELATED_PROMPT_PATH = os.environ.get("IS_RELATED_PROMPT_PATH")
IS_SELF_CONTAINED_PROMPT_PATH = os.environ.get("IS_SELF_CONTAINED_PROMPT_PATH")
IS_QUESTION_PROMPT_PATH = os.environ.get("IS_QUESTION_PROMPT_PATH")
LANGUAGE_IS_CLEAR_PROMPT_PATH = os.environ.get("LANGUAGE_IS_CLEAR_PROMPT_PATH")
ANSWERS_ARE_ALL_DIFFERENT_PROMPT_PATH = os.environ.get(
    "ANSWERS_ARE_ALL_DIFFERENT_PROMPT_PATH"
)
FAKE_ANSWERS_ARE_NOT_OBVIOUS_PROMPT_PATH = os.environ.get(
    "FAKE_ANSWERS_ARE_NOT_OBVIOUS_PROMPT_PATH"
)
ANSWERS_ARE_RELATED_PROMPT_PATH = os.environ.get("ANSWERS_ARE_RELATED_PROMPT_PATH")
QUIZ_ABOUT_CONCEPT_PROMPT_PATH = os.environ.get("QUIZ_ABOUT_CONCEPT_PROMPT_PATH")

app = FastAPI(
    title="Quiz Generation API",
    version="0.0.1",
    description="Generate quizzes from texts",
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
connector = APIConnectorWithOpenAIFormat(
    api_url=VLLM_API_URL,
    cache_path=VLLM_CACHE_PATH,
)
openai_connector = CustomOpenAIConnector(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    cache_path=OPEN_AI_CACHE_PATH,
)
metadata_prompt_config = MetadataPromptsConfig(
    summary_prompt_path=SUMMARY_PROMPT_PATH,
    title_prompt_path=TITLE_PROMPT_PATH,
    description_prompt_path=DESCRIPTION_PROMPT_PATH,
    generate_topics_prompt_path=GENERATE_TOPICS_PROMPT_PATH,
    discipline_prompt_path=DISCIPLINE_PROMPT_PATH,
)
prompts_config = QuizPromptsConfig(
    quiz_generation_prompt=QUIZ_GENERATION_PROMPT_PATH,
)
evaluation_prompts_config = EvaluationPromptsConfig(
    is_related_prompt=IS_RELATED_PROMPT_PATH,
    is_self_contained_prompt=IS_SELF_CONTAINED_PROMPT_PATH,
    is_question_prompt=IS_QUESTION_PROMPT_PATH,
    language_is_clear_prompt=LANGUAGE_IS_CLEAR_PROMPT_PATH,
    answers_are_all_different_prompt=ANSWERS_ARE_ALL_DIFFERENT_PROMPT_PATH,
    fake_answers_are_not_obvious_prompt=FAKE_ANSWERS_ARE_NOT_OBVIOUS_PROMPT_PATH,
    answers_are_related=ANSWERS_ARE_RELATED_PROMPT_PATH,
    quiz_about_concept=QUIZ_ABOUT_CONCEPT_PROMPT_PATH,
)


@app.get("/")
def root():
    return {"message": "Welcome to the quiz generation API."}


@app.get("/health", tags=["health"])
def health():
    return True


def generate_quizzes(
    language: str, disciplines: List[str], sentences: List[str]
) -> QuizzesWrapper:
    metadata = metadata_generation(
        transcripts=sentences,
        language=language,
        model_name=MODEL_NAME,
        tokenizer=tokenizer,
        connector=connector,
        prompts_config=metadata_prompt_config,
        disciplines=disciplines,
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


# TODO: Evaluate quizzes
def evaluate_quizzes(quizzes: QuizzesWrapper, language: str = "fr"):
    title = quizzes.enrichment_version_metadata.title
    description = quizzes.enrichment_version_metadata.description
    evaluator = Evaluator(
        model_name=EVALUATION_MODEL_NAME,
        course_metadata=MetaData(
            title=title,
            description=description,
        ),
        tokenizer=tokenizer,
        connector=openai_connector,
        language=language,
        prompts_config=evaluation_prompts_config,
    )
    reformated_quizzes = [
        MultipleAnswerQuiz(
            question=quiz.question,
            answer=quiz.choices[0].option_text,
            fake_answer_1=quiz.choices[1].option_text,
            fake_answer_2=quiz.choices[2].option_text,
            fake_answer_3=quiz.choices[3].option_text,
            explanation=quiz.explanation,
        )
        for quiz in quizzes.multiple_choice_questions
    ]
    evaluations = evaluator.evaluate_quizzes(reformated_quizzes)
    return EvaluationsWrapper(evaluations=evaluations)


@app.post("/generate-quizzes", response_model=QuizzesWrapper)
def generate(transcript: TranscriptWrapper):
    disciplines = transcript.disciplines
    sentences = [sentence.text for sentence in transcript.transcript.sentences]
    return generate_quizzes(transcript.transcript.language, disciplines, sentences)


@app.post("/evaluate-quizzes", response_model=EvaluationsWrapper)
def evaluate(quizzes: QuizzesWrapper):
    return evaluate_quizzes(quizzes)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
