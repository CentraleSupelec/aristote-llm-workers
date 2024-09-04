from typing import List, Optional

from transformers import PreTrainedTokenizerBase

from aristote.connectors.connectors import AbstractConnector
from aristote.dtos import MetaData, TranscribedText
from aristote.quiz_generation.quiz_generator import MultipleAnswerQuiz
from aristote.translation_generation.translation_generator import (
    TranslationGenerator,
    TranslationPromptsConfig,
    TranslationResult,
)


def translation_generation(
    meta_data: MetaData,
    transcripts: List[TranscribedText],
    quizzes: List[MultipleAnswerQuiz],
    notes: str,
    from_language: str,
    to_language: str,
    model_name: str,
    tokenizer: PreTrainedTokenizerBase,
    connector: AbstractConnector,
    prompts_config: TranslationPromptsConfig,
    debug: bool = False,
    batch_size: Optional[int] = None,
) -> TranslationResult:

    if debug:
        print(transcripts)
        print("=======================================================")

    translation_generator = TranslationGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        debug=False,
        topics=meta_data.main_topics if meta_data is not None else None,
        batch_size=batch_size,
    )
    translation = translation_generator.generate_translation(
        quizzes=quizzes,
        meta_data=meta_data,
        transcripts=transcripts,
        notes=notes,
        from_language=from_language,
        to_language=to_language,
    )
    return translation


def main():
    # TODO: Finish translation from file paths
    return
