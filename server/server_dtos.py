from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from aristote.evaluation.evaluator import EvaluatedQuiz


class Word(BaseModel):
    id: Optional[int] = None
    start: float
    end: float
    text: str


class Sentence(BaseModel):
    id: Optional[int] = None
    is_transient: Optional[bool] = None
    no_speech_prob: Optional[float] = None
    no_caption_prob: Optional[float] = None
    start: float
    end: float
    text: str
    words: Optional[List[Word]] = None


class Transcript(BaseModel):
    original_file_name: Optional[str] = None
    language: Optional[str] = None
    text: str
    sentences: List[Sentence]


class TranscriptWrapper(BaseModel):
    enrichment_version_id: str
    transcript: Transcript


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class EnrichmentVersionMetadata(BaseSchema):
    title: str
    description: str
    topics: Optional[List[str]] = None
    discipline: Optional[str] = None
    media_type: Optional[str] = None


class Choice(BaseSchema):
    id: Optional[str] = None
    option_text: str
    correct_answer: bool


class AnswerPointer(BaseSchema):
    start_answer_pointer: Optional[str] = None
    stop_answer_pointer: Optional[str] = None


class MultipleChoiceQuestion(BaseSchema):
    id: Optional[str] = None
    question: str
    explanation: str
    choices: List[Choice]
    answer_pointer: Optional[AnswerPointer] = None


class QuizzesWrapper(BaseSchema):
    enrichment_version_metadata: Optional[EnrichmentVersionMetadata] = None
    multiple_choice_questions: List[MultipleChoiceQuestion] = None
    notes: Optional[str] = None
    task_id: Optional[str] = None
    failure_cause: Optional[str] = None
    status: Optional[str] = "OK"


class EvaluationsWrapper(BaseSchema):
    evaluations: List[EvaluatedQuiz]
    task_id: Optional[str] = None
    failure_cause: Optional[str] = None
    status: Optional[str] = "OK"


class TranslationWrapper(BaseSchema):
    enrichment_version_metadata: Optional[EnrichmentVersionMetadata] = None
    multiple_choice_questions: List[MultipleChoiceQuestion]
    transcript: Transcript
    notes: Optional[str] = None


class TranslationInputtWrapper(TranslationWrapper):
    from_language: str
    to_language: str


class TranslationOutputWrapper(TranslationWrapper):
    task_id: Optional[str] = None
    failure_cause: Optional[str] = None
    status: Optional[str] = "OK"
