from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import List, Literal, Tuple

from pydantic import BaseModel
from tqdm import tqdm
from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector, Prompt
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.preprocessing.preprocessing import (
    get_splits,
)
from quiz_generation.reformulation.reformulation import create_reformulations

BATCH_SIZE = 16


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


class QuizEvaluationPromptsConfig(BaseModel):
    # Question
    is_related_prompt: str
    is_self_contained_prompt: str
    is_question_prompt: str
    language_is_clear_prompt: str
    non_undefined_symbols_in_question_prompt: str
    # Answers
    answers_are_all_different_prompt: str
    fake_answers_are_not_obvious_prompt: str


class QuizPromptsConfig(BaseModel):
    quiz_generation_prompt: str
    quiz_evaluation_prompts_config: QuizEvaluationPromptsConfig


class QuizGenerator:
    def __init__(
        self,
        model_name: str,
        course_metadata: MetaData,
        tokenizer: AutoTokenizer,
        api_connector: APIConnector,
        language: Literal["fr", "en"],
        prompts_config: QuizPromptsConfig,
    ) -> None:
        self.model_name = model_name
        self.course_metadata = course_metadata
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.language = language

        with open(prompts_config.quiz_generation_prompt, "r", encoding="utf-8") as file:
            self.quiz_generation_prompt = file.read()

        with open(
            prompts_config.quiz_evaluation_prompts_config.is_related_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_related_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.is_self_contained_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_self_contained_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.is_question_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_question_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.language_is_clear_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.language_is_clear_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.non_undefined_symbols_in_question_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.non_undefined_symbols_in_question_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.answers_are_all_different_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.answers_are_all_different_prompt = file.read()
        with open(
            prompts_config.quiz_evaluation_prompts_config.fake_answers_are_not_obvious_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.fake_answers_are_not_obvious_prompt = file.read()

    def generate_quiz(self, reformulation: str, quiz_type: QuizType) -> str:
        if "[EXTRACT]" not in self.quiz_generation_prompt:
            raise ValueError("Title prompt must contain [EXTRACT]")
        conv = [
            {
                "role": "user",
                "content": self.quiz_generation_prompt.replace(
                    "[EXTRACT]", reformulation
                ),
            }
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        question = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=100,
                temperature=0,
            )
        )
        if "?" in question:
            question = question.split("?")[0]
            question += "?"

        if self.language == "fr":
            answer_prompt = "Réponse:"
        elif self.language == "en":
            answer_prompt = "Answer:"

        conv += [
            {"role": "assistant", "content": question},
            {"role": "user", "content": answer_prompt},
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        answer = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0,
                stop=["."],
            )
        )
        answer += "."

        if self.language == "fr":
            fake_answer_prompt_1 = "Fausse Réponse 1:"
        elif self.language == "en":
            fake_answer_prompt_1 = "Fake Answer 1:"

        conv += [
            {"role": "assistant", "content": answer},
            {"role": "user", "content": fake_answer_prompt_1},
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        fake_answer_1 = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.1,
                stop=["."],
            )
        )
        fake_answer_1 += "."

        if self.language == "fr":
            fake_answer_prompt_2 = "Fausse Réponse 2:"
        elif self.language == "en":
            fake_answer_prompt_2 = "Fake Answer 2:"

        conv += [
            {"role": "assistant", "content": fake_answer_1},
            {"role": "user", "content": fake_answer_prompt_2},
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        fake_answer_2 = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.1,
                stop=["."],
            )
        )
        fake_answer_2 += "."

        if self.language == "fr":
            fake_answer_prompt_3 = "Fausse Réponse 3:"
        elif self.language == "en":
            fake_answer_prompt_3 = "Fake Answer 3:"
        conv += [
            {"role": "assistant", "content": fake_answer_2},
            {"role": "user", "content": fake_answer_prompt_3},
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        fake_answer_3 = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.1,
                stop=["."],
            )
        )
        fake_answer_3 += "."

        if self.language == "fr":
            explanation = "Explication:"
        elif self.language == "en":
            explanation = "Explanation:"
        conv += [
            {"role": "assistant", "content": fake_answer_3},
            {"role": "user", "content": explanation},
        ]
        text = self.tokenizer.apply_chat_template(
            conversation=conv, tokenize=False, add_generation_prompt=True
        )
        explanation = self.api_connector.generate(
            Prompt(
                text=text,
                model_name=self.model_name,
                max_tokens=800,
                temperature=0.1,
            )
        )
        return MultipleAnswerQuiz(
            question=question,
            answer=answer,
            fake_answer_1=fake_answer_1,
            fake_answer_2=fake_answer_2,
            fake_answer_3=fake_answer_3,
            explanation=explanation,
            quiz_type=quiz_type,
            quiz_origin_text=reformulation,
        )

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
        batch_size: int = BATCH_SIZE,
    ) -> List[MultipleAnswerQuiz]:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Send requests in batches
            ma_quizzes = list(
                tqdm(
                    executor.map(
                        lambda extract: self.generate_quiz(extract, quiz_type), extracts
                    ),
                    total=len(extracts),
                    desc="Generating quizzes",
                )
            )
        return ma_quizzes

    def evaluate_quiz(
        self,
        quiz: MultipleAnswerQuiz,
    ) -> QuizEvaluation:
        prompts_texts = {
            "is_related": self.is_related_prompt,
            "is_self_contained": self.is_self_contained_prompt,
            "is_question": self.is_question_prompt,
            "language_is_clear": self.language_is_clear_prompt,
            "non_undefined_symbols_in_question": (
                self.non_undefined_symbols_in_question_prompt
            ),
            "answers_are_all_different": self.answers_are_all_different_prompt,
            "fake_answers_are_not_obvious": self.fake_answers_are_not_obvious_prompt,
        }
        eval_results = {}
        for eval_name, prompt_template in prompts_texts.items():
            answers = "\n".join(
                [
                    "- " + fake_answer
                    for fake_answer in [
                        quiz.answer,
                        quiz.fake_answer_1,
                        quiz.fake_answer_2,
                        quiz.fake_answer_3,
                    ]
                ]
            )
            fake_answers = "\n".join(
                [
                    "- " + fake_answer
                    for fake_answer in [
                        quiz.fake_answer_1,
                        quiz.fake_answer_2,
                        quiz.fake_answer_3,
                    ]
                ]
            )
            if "[TITLE]" not in prompt_template:
                raise ValueError("Title prompt must contain [TITLE]")
            if "[DESCRIPTION]" not in prompt_template:
                raise ValueError("Title prompt must contain [DESCRIPTION]")
            if "[QUESTION]" not in prompt_template:
                raise ValueError("Title prompt must contain [QUESTION]")
            prompts_texts[eval_name] = (
                prompt_template.replace("[TITLE]", self.course_metadata.title)
                .replace("[DESCRIPTION]", self.course_metadata.description)
                .replace("[QUESTION]", quiz.question)
                .replace("[ANSWER]", quiz.answer)
                .replace("[ANSWERS]", answers)
                .replace("[FAKE ANSWERS]", fake_answers)
            )
            prompt = Prompt(
                text=prompts_texts[eval_name],
                model_name=self.model_name,
                max_tokens=10,
                temperature=0,
            )
            result_str_1 = self.api_connector.generate(prompt).strip().lower()
            if self.language == "fr":
                if "non" in result_str_1:
                    result = False
                elif "oui" in result_str_1:
                    result = True
                else:
                    result = False
            elif self.language == "en":
                if "no" in result_str_1:
                    result = False
                elif "yes" in result_str_1:
                    result = True
                else:
                    result = False
            else:
                raise ValueError("Language must be 'en' or 'fr'")
            eval_results[eval_name] = result
        int_values = [int(x) for x in eval_results.values()]
        eval_results["score"] = sum(int_values)
        return QuizEvaluation(**eval_results)

    def evaluate_quizzes(
        self,
        quizzes: List[MultipleAnswerQuiz],
        batch_size: int = BATCH_SIZE,
    ) -> List[QuizEvaluation]:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Send requests in batches
            quiz_evaluations = list(
                tqdm(
                    executor.map(self.evaluate_quiz, quizzes),
                    total=len(quizzes),
                    desc="Generating evaluations",
                )
            )
        return quiz_evaluations

    def full_generation(
        self,
        transcripts: List[str],
    ) -> List[EvaluatedQuiz]:
        short_reformulations, long_reformulations = self.generate_reformulations(
            transcripts
        )
        local_quizzes = self.generate_quizzes(short_reformulations, QuizType.LOCAL)
        global_quizzes = self.generate_quizzes(long_reformulations, QuizType.GLOBAL)
        quiz_evals = self.evaluate_quizzes(local_quizzes + global_quizzes)
        evaluated_quizzes = [
            EvaluatedQuiz(quiz=quiz, evaluation=quiz_eval)
            for quiz, quiz_eval in zip(local_quizzes + global_quizzes, quiz_evals)
        ]
        return evaluated_quizzes
