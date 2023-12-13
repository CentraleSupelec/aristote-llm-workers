from typing import List, Optional

from pydantic import BaseModel


class Sentence(BaseModel):
    id: int
    is_transient: Optional[bool]
    no_speech_prob: float
    no_caption_prob: Optional[float]
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
    discipline: str
    media_type: str


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
    task_id: str
    failure_cause: str
    status: str
