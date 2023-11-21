from enum import Enum
from typing import List, Literal, Tuple, Union

from illuin_llm_tools import Message
from pydantic import BaseModel
from transformers import PreTrainedTokenizerBase
from tiktoken import Encoding

from quiz_generation.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
)
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.preprocessing.preprocessing import (
    get_splits,
)
from quiz_generation.reformulation.reformulation import create_reformulations

BATCH_SIZE = 4


class QuizType(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"


class MultipleAnswerQuiz(BaseModel):
    question: str  # = Field(min_length=1)
    answer: str  # = Field(min_length=1)
    fake_answer_1: str  # = Field(min_length=1)
    fake_answer_2: str  # = Field(min_length=1)
    fake_answer_3: str  # = Field(min_length=1)
    explanation: str  # = Field(min_length=1)
    quiz_type: QuizType
    quiz_origin_text: str


class QuizEvaluation(BaseModel):
    # Question
    is_related: bool
    is_self_contained: bool
    is_question: bool
    language_is_clear: bool
    non_undefined_symbols_in_question: bool
    # Answers
    answers_are_all_different: bool
    fake_answers_are_not_obvious: bool
    # Sum of checked criteria
    score: int


class EvaluatedQuiz(BaseModel):
    quiz: MultipleAnswerQuiz
    evaluation: QuizEvaluation


class QuizPromptsConfig(BaseModel):
    quiz_generation_prompt: str


class QuizGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: Union[PreTrainedTokenizerBase, Encoding],
        api_connector: AbstractConnector,
        language: Literal["fr", "en"],
        prompts_config: QuizPromptsConfig,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.language = language

        with open(prompts_config.quiz_generation_prompt, "r", encoding="utf-8") as file:
            self.quiz_generation_prompt = file.read()

    def get_custom_prompt(self, conv: List[dict]) -> CustomPrompt:
        if isinstance(self.tokenizer, PreTrainedTokenizerBase):
            text = self.tokenizer.apply_chat_template(
                conversation=conv, tokenize=False, add_generation_prompt=True
            )
            prompt_input = CustomPrompt(
                text=text,
                parameters=CustomPromptParameters(
                    model_name=self.model_name,
                    max_tokens=100,
                    temperature=0,
                ),
            )
        else:
            prompt_input = CustomPrompt(
                messages=[Message(**message) for message in conv],
                parameters=CustomPromptParameters(
                    model_name=self.model_name,
                    max_tokens=100,
                    temperature=0,
                ),
            )
        return prompt_input

    def generate_reformulations(
        self,
        transcripts: List[str],
    ) -> Tuple[List[str], List[str]]:
        short_transcripts = get_splits(
            transcripts, tokenizer=self.tokenizer, max_length=1000
        )
        short_reformulations = create_reformulations(
            short_transcripts,
            self.model_name,
            self.tokenizer,
            self.api_connector,
            self.language,
        )
        long_transcripts = get_splits(
            transcripts, tokenizer=self.tokenizer, max_length=2000
        )
        long_reformulations = create_reformulations(
            long_transcripts,
            self.model_name,
            self.tokenizer,
            self.api_connector,
            self.language,
        )
        return short_reformulations, long_reformulations

    def generate_quizzes(
        self,
        extracts: List[str],
        quiz_type: QuizType,
    ) -> List[MultipleAnswerQuiz]:
        # Get Questions
        if "[EXTRACT]" not in self.quiz_generation_prompt:
            raise ValueError("Title prompt must contain [EXTRACT]")
        conversations = [
            [
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.replace(
                        "[EXTRACT]", extract
                    ),
                }
            ]
            for extract in extracts
        ]
        questions = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating questions",
        )
        for i, question in enumerate(questions):
            if "?" in question:
                questions[i] = question.split("?")[0]
                questions[i] += "?"

        if self.language == "fr":
            answer_prompt = "Réponse:"
        elif self.language == "en":
            answer_prompt = "Answer:"

        for i, question in enumerate(questions):
            conversations[i] += [
                {"role": "assistant", "content": question},
                {"role": "user", "content": answer_prompt},
            ]
        answers = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating answers",
        )
        answers = [answer + "." for answer in answers]

        if self.language == "fr":
            fake_answer_prompt_1 = "Fausse Réponse 1:"
        elif self.language == "en":
            fake_answer_prompt_1 = "Fake Answer 1:"

        for i, answer in enumerate(answers):
            conversations[i] += [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": fake_answer_prompt_1},
            ]
        fake_answers_1 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 1",
        )
        fake_answers_1 = [fake_answer + "." for fake_answer in fake_answers_1]

        if self.language == "fr":
            fake_answer_prompt_2 = "Fausse Réponse 2:"
        elif self.language == "en":
            fake_answer_prompt_2 = "Fake Answer 2:"

        for i, fa_1 in enumerate(fake_answers_1):
            conversations[i] += [
                {"role": "assistant", "content": fa_1},
                {"role": "user", "content": fake_answer_prompt_2},
            ]
        fake_answers_2 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 2",
        )
        fake_answers_2 = [fake_answer + "." for fake_answer in fake_answers_2]

        if self.language == "fr":
            fake_answer_prompt_3 = "Fausse Réponse 3:"
        elif self.language == "en":
            fake_answer_prompt_3 = "Fake Answer 3:"

        for i, fa_2 in enumerate(fake_answers_2):
            conversations[i] += [
                {"role": "assistant", "content": fa_2},
                {"role": "user", "content": fake_answer_prompt_3},
            ]
        fake_answers_3 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 3",
        )
        fake_answers_3 = [fake_answer + "." for fake_answer in fake_answers_3]

        if self.language == "fr":
            explanation = "Explication:"
        elif self.language == "en":
            explanation = "Explanation:"
        for i, fa_3 in enumerate(fake_answers_3):
            conversations[i] += [
                {"role": "assistant", "content": fa_3},
                {"role": "user", "content": explanation},
            ]
        explanations = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating explanations",
        )
        return [
            MultipleAnswerQuiz(
                question=question,
                answer=answer,
                fake_answer_1=fake_answer_1,
                fake_answer_2=fake_answer_2,
                fake_answer_3=fake_answer_3,
                explanation=explanation,
                quiz_type=quiz_type,
                quiz_origin_text=reformulation,
            )
            for (
                question,
                answer,
                fake_answer_1,
                fake_answer_2,
                fake_answer_3,
                explanation,
                reformulation,
            ) in zip(
                questions,
                answers,
                fake_answers_1,
                fake_answers_2,
                fake_answers_3,
                explanations,
                extracts,
            )
        ]

    def full_generation(
        self,
        transcripts: List[str],
    ) -> List[MultipleAnswerQuiz]:
        short_reformulations, long_reformulations = self.generate_reformulations(
            transcripts
        )
        local_quizzes = self.generate_quizzes(short_reformulations, QuizType.LOCAL)
        global_quizzes = self.generate_quizzes(long_reformulations, QuizType.GLOBAL)
        return local_quizzes + global_quizzes
