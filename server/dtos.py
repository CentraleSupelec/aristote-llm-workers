from typing import List, Optional

from pydantic import BaseModel

from quiz_generation.evaluation.evaluator import EvaluatedQuiz


class Sentence(BaseModel):
    id: Optional[int] = None
    is_transient: Optional[bool] = None
    no_speech_prob: float
    no_caption_prob: Optional[float] = None
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    original_file_name: str
    language: str
    text: str
    sentences: List[Sentence]


class TranscriptWrapper(BaseModel):
    enrichment_version_id: str
    transcript: Transcript
    media_types: List[str]
    disciplines: List[str]


class EnrichmentVersionMetadata(BaseModel):
    title: str
    description: str
    topics: List[str]
    discipline: Optional[str] = None
    media_type: Optional[str] = None


class Choice(BaseModel):
    option_text: str
    correct_answer: bool


class MultipleChoiceQuestion(BaseModel):
    question: str
    explanation: str
    choices: List[Choice]


class QuizzesWrapper(BaseModel):
    enrichment_version_metadata: EnrichmentVersionMetadata
    multiple_choice_questions: List[MultipleChoiceQuestion]
    task_id: Optional[str] = None
    failure_cause: Optional[str] = None
    status: Optional[str] = None


class EvaluationsWrapper(BaseModel):
    evaluations: List[EvaluatedQuiz]
    task_id: Optional[str] = None
    failure_cause: Optional[str] = None
    status: Optional[str] = None
