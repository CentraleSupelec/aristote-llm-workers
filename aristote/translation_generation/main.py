from typing import List, Optional

from transformers import PreTrainedTokenizerBase

from aristote.connectors.connectors import AbstractConnector
from aristote.dtos import MetaData, TranscribedText
from aristote.preprocessing.preprocessing import (
    get_splits,
)
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
    from_language: str,
    to_language: str,
    model_name: str,
    tokenizer: PreTrainedTokenizerBase,
    connector: AbstractConnector,
    prompts_config: TranslationPromptsConfig,
    debug: bool = False,
    batch_size: Optional[int] = None,
) -> TranslationResult:
    new_transcripts = get_splits(transcripts, tokenizer=tokenizer)
    if len(new_transcripts) > 20:
        new_transcripts = get_splits(transcripts, tokenizer=tokenizer, max_length=3000)
    if len(new_transcripts) > 20:
        raise ValueError(f"Too many splits {len(new_transcripts)}")

    print("Number of splits:", len(new_transcripts))

    if debug:
        print(new_transcripts)
        print("=======================================================")

    translation_generator = TranslationGenerator(
        model_name=model_name,
        tokenizer=tokenizer,
        api_connector=connector,
        prompts_config=prompts_config,
        debug=True,
        topics=meta_data.main_topics,
        batch_size=batch_size,
    )
    translation = translation_generator.generate_translation(
        quizzes=quizzes,
        meta_data=meta_data,
        transcripts=new_transcripts,
        from_language=from_language,
        to_language=to_language,
    )
    return translation


def main():
    # TODO: Finish translation from file paths
    return
