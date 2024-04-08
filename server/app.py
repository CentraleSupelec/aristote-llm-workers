import os
from datetime import datetime, timedelta
from typing import List, Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from transformers import AutoTokenizer

from aristote.connectors.connectors import (
    APIConnectorWithOpenAIFormat,
    CustomOpenAIConnector,
)
from aristote.dtos import TranscribedText
from aristote.evaluation.evaluator import EvaluationPromptsConfig, Evaluator
from aristote.metadata_generation.main import metadata_generation
from aristote.metadata_generation.metadata_generator import (
    MetaData,
    MetadataPromptsConfig,
)
from aristote.quiz_generation.quiz_generator import (
    MultipleAnswerQuiz,
    QuizGenerator,
    QuizPromptsConfig,
)
from server.server_dtos import (
    AnswerPointer,
    Choice,
    EnrichmentVersionMetadata,
    EvaluationsWrapper,
    MultipleChoiceQuestion,
    QuizzesWrapper,
    TranscriptWrapper,
)

load_dotenv(".env")

MODEL_NAME = os.environ["MODEL_NAME"]
VLLM_API_URL = os.environ["VLLM_API_URL"]
VLLM_CACHE_PATH = os.environ["VLLM_CACHE_PATH"]

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID")
OPEN_AI_CACHE_PATH = os.environ.get("OPEN_AI_CACHE_PATH")
EVALUATION_MODEL_NAME = os.environ["EVALUATION_MODEL_NAME"]

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
    cache_path=os.environ["OPEN_AI_CACHE_PATH"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Welcome to the quiz generation API."}


@app.get("/health", tags=["health"])
def health() -> bool:
    return True


def format_time(seconds: int):
    duration = timedelta(seconds=seconds)
    base_date = datetime(1900, 1, 1)
    result_date = base_date + duration
    result_string = result_date.strftime("%H:%M:%S")
    return result_string


def generate_quizzes(
    language: str,
    disciplines: List[str],
    media_types: List[str],
    transcripts: List[TranscribedText],
) -> QuizzesWrapper:
    if language == "fr":
        metadata_prompt_config = MetadataPromptsConfig(
            reformulation_prompt_path=os.environ["REFORMULATION_PROMPT_PATH_FR"],
            summary_prompt_path=os.environ["SUMMARY_PROMPT_PATH_FR"],
            title_prompt_path=os.environ["TITLE_PROMPT_PATH_FR"],
            description_prompt_path=os.environ["DESCRIPTION_PROMPT_PATH_FR"],
            generate_topics_prompt_path=os.environ["GENERATE_TOPICS_PROMPT_PATH_FR"],
            discipline_prompt_path=os.environ["DISCIPLINE_PROMPT_PATH_FR"],
            media_type_prompt_path=os.environ["MEDIA_TYPE_PROMPT_PATH_FR"],
            local_media_type_prompt_path=os.environ["LOCAL_MEDIA_TYPE_PROMPT_PATH_FR"],
        )
        prompts_config = QuizPromptsConfig(
            quiz_generation_prompt=os.environ["QUIZ_GENERATION_PROMPT_PATH_FR"],
            reformulation_prompt_path=os.environ["REFORMULATION_PROMPT_PATH_FR"],
        )
    elif language == "en":
        metadata_prompt_config = MetadataPromptsConfig(
            reformulation_prompt_path=os.environ["REFORMULATION_PROMPT_PATH_EN"],
            summary_prompt_path=os.environ["SUMMARY_PROMPT_PATH_EN"],
            title_prompt_path=os.environ["TITLE_PROMPT_PATH_EN"],
            description_prompt_path=os.environ["DESCRIPTION_PROMPT_PATH_EN"],
            generate_topics_prompt_path=os.environ["GENERATE_TOPICS_PROMPT_PATH_EN"],
            discipline_prompt_path=os.environ["DISCIPLINE_PROMPT_PATH_EN"],
            media_type_prompt_path=os.environ["MEDIA_TYPE_PROMPT_PATH_EN"],
            local_media_type_prompt_path=os.environ["LOCAL_MEDIA_TYPE_PROMPT_PATH_EN"],
        )
        prompts_config = QuizPromptsConfig(
            quiz_generation_prompt=os.environ["QUIZ_GENERATION_PROMPT_PATH_EN"],
            reformulation_prompt_path=os.environ["REFORMULATION_PROMPT_PATH_EN"],
        )
    else:
        raise ValueError(f"Language {language} not supported.")

    metadata = metadata_generation(
        transcripts=transcripts,
        model_name=MODEL_NAME,
        tokenizer=tokenizer,
        connector=connector,
        prompts_config=metadata_prompt_config,
        disciplines=disciplines,
        media_types=media_types,
    )
    quiz_generator = QuizGenerator(
        model_name=MODEL_NAME,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        chunks_path=None,
    )
    quizzes = quiz_generator.full_generation(transcripts)
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
            answer_pointer=AnswerPointer(
                start_answer_pointer=format_time(quiz.origin_start),
                stop_answer_pointer=format_time(quiz.origin_end),
            ),
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
def evaluate_quizzes(
    quizzes: QuizzesWrapper, language: Literal["fr", "en"] = "fr"
) -> EvaluationsWrapper:
    if language == "fr":
        evaluation_prompts_config = EvaluationPromptsConfig(
            is_related_prompt=os.environ["IS_RELATED_PROMPT_PATH_FR"],
            is_self_contained_prompt=os.environ["IS_SELF_CONTAINED_PROMPT_PATH_FR"],
            is_question_prompt=os.environ["IS_QUESTION_PROMPT_PATH_FR"],
            language_is_clear_prompt=os.environ["LANGUAGE_IS_CLEAR_PROMPT_PATH_FR"],
            answers_are_all_different_prompt=os.environ[
                "ANSWERS_ARE_ALL_DIFFERENT_PROMPT_PATH_FR"
            ],
            fake_answers_are_not_obvious_prompt=os.environ[
                "FAKE_ANSWERS_ARE_NOT_OBVIOUS_PROMPT_PATH_FR"
            ],
            answers_are_related=os.environ["ANSWERS_ARE_RELATED_PROMPT_PATH_FR"],
            quiz_about_concept=os.environ["QUIZ_ABOUT_CONCEPT_PROMPT_PATH_FR"],
        )
    elif language == "en":
        evaluation_prompts_config = EvaluationPromptsConfig(
            is_related_prompt=os.environ["IS_RELATED_PROMPT_PATH_EN"],
            is_self_contained_prompt=os.environ["IS_SELF_CONTAINED_PROMPT_PATH_EN"],
            is_question_prompt=os.environ["IS_QUESTION_PROMPT_PATH_EN"],
            language_is_clear_prompt=os.environ["LANGUAGE_IS_CLEAR_PROMPT_PATH_EN"],
            answers_are_all_different_prompt=os.environ[
                "ANSWERS_ARE_ALL_DIFFERENT_PROMPT_PATH_EN"
            ],
            fake_answers_are_not_obvious_prompt=os.environ[
                "FAKE_ANSWERS_ARE_NOT_OBVIOUS_PROMPT_PATH_EN"
            ],
            answers_are_related=os.environ["ANSWERS_ARE_RELATED_PROMPT_PATH_EN"],
            quiz_about_concept=os.environ["QUIZ_ABOUT_CONCEPT_PROMPT_PATH_EN"],
        )
    else:
        raise ValueError(f"Language {language} not supported.")
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
            id=quiz.id,
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
def generate(transcript: TranscriptWrapper) -> QuizzesWrapper:
    disciplines = transcript.disciplines
    media_types = transcript.media_types
    transcribed_sentences = [
        TranscribedText(
            text=sentence.text,
            start=sentence.start,
            end=sentence.end,
        )
        for sentence in transcript.transcript.sentences
    ]
    return generate_quizzes(
        transcript.transcript.language, disciplines, media_types, transcribed_sentences
    )


@app.post("/evaluate-quizzes", response_model=EvaluationsWrapper)
def evaluate(quizzes: QuizzesWrapper) -> EvaluationsWrapper:
    return evaluate_quizzes(quizzes)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
