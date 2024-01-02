from typing import Any, Dict, List, Literal

from pydantic import BaseModel
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
)
from quiz_generation.metadata_generation.metadata_generator import MetaData
from quiz_generation.quiz_generation.quiz_generator import MultipleAnswerQuiz


class QuizEvaluation(BaseModel):
    # Question
    is_related: bool
    is_self_contained: bool
    is_question: bool
    language_is_clear: bool
    # Answers
    answers_are_all_different: bool
    fake_answers_are_not_obvious: bool
    answers_are_related: bool
    # Quiz
    quiz_about_concept: bool
    # Sum of checked criteria
    score: int


class EvaluatedQuiz(BaseModel):
    quiz: MultipleAnswerQuiz
    evaluation: QuizEvaluation


class EvaluationPromptsConfig(BaseModel):
    # Question
    is_related_prompt: str
    is_self_contained_prompt: str
    is_question_prompt: str
    language_is_clear_prompt: str
    # Answers
    answers_are_all_different_prompt: str
    fake_answers_are_not_obvious_prompt: str
    answers_are_related: str
    # Quiz
    quiz_about_concept: str


class Evaluator:
    def __init__(
        self,
        model_name: str,
        course_metadata: MetaData,
        tokenizer: AutoTokenizer,
        connector: AbstractConnector,
        language: Literal["fr", "en"],
        prompts_config: EvaluationPromptsConfig,
    ) -> None:
        self.model_name = model_name
        self.course_metadata = course_metadata
        self.tokenizer = tokenizer
        self.connector = connector
        self.language = language

        # self.evaluation_prompts =
        # for prompt_path in prompt_paths:
        with open(
            prompts_config.is_related_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_related_prompt = file.read()
        with open(
            prompts_config.is_self_contained_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_self_contained_prompt = file.read()
        with open(
            prompts_config.is_question_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.is_question_prompt = file.read()
        with open(
            prompts_config.language_is_clear_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.language_is_clear_prompt = file.read()
        with open(
            prompts_config.answers_are_all_different_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.answers_are_all_different_prompt = file.read()
        with open(
            prompts_config.fake_answers_are_not_obvious_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.fake_answers_are_not_obvious_prompt = file.read()
        with open(
            prompts_config.fake_answers_are_not_obvious_prompt,
            "r",
            encoding="utf-8",
        ) as file:
            self.fake_answers_are_not_obvious_prompt = file.read()
        with open(prompts_config.answers_are_related, "r", encoding="utf-8") as file:
            self.answers_are_related = file.read()
        with open(prompts_config.quiz_about_concept, "r", encoding="utf-8") as file:
            self.quiz_about_concept = file.read()

    def evaluate_quizzes(
        self,
        quizzes: List[MultipleAnswerQuiz],
    ) -> List[EvaluatedQuiz]:
        prompts_texts = {
            "is_related": self.is_related_prompt,
            "is_self_contained": self.is_self_contained_prompt,
            "is_question": self.is_question_prompt,
            "language_is_clear": self.language_is_clear_prompt,
            "answers_are_all_different": self.answers_are_all_different_prompt,
            "fake_answers_are_not_obvious": self.fake_answers_are_not_obvious_prompt,
            "answers_are_related": self.answers_are_related,
            "quiz_about_concept": self.quiz_about_concept,
        }
        all_eval_results: List[Dict[str, Any]] = [{} for _ in quizzes]
        for eval_name, prompt_template in prompts_texts.items():
            all_answers = [
                "\n".join(
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
                for quiz in quizzes
            ]
            all_fake_answers = [
                "\n".join(
                    [
                        "- " + fake_answer
                        for fake_answer in [
                            quiz.fake_answer_1,
                            quiz.fake_answer_2,
                            quiz.fake_answer_3,
                        ]
                    ]
                )
                for quiz in quizzes
            ]
            if "[TITLE]" not in prompt_template:
                raise ValueError("Title prompt must contain [TITLE]")
            if "[DESCRIPTION]" not in prompt_template:
                raise ValueError("Title prompt must contain [DESCRIPTION]")
            if "[QUESTION]" not in prompt_template:
                raise ValueError("Title prompt must contain [QUESTION]")

            prompt_texts = [
                (
                    prompt_template.replace("[TITLE]", self.course_metadata.title)
                    .replace("[DESCRIPTION]", self.course_metadata.description)
                    .replace("[QUESTION]", quiz.question)
                    .replace("[ANSWER]", quiz.answer)
                    .replace("[ANSWERS]", answers)
                    .replace("[FAKE ANSWERS]", fake_answers)
                )
                for quiz, answers, fake_answers in zip(
                    quizzes, all_answers, all_fake_answers
                )
            ]
            prompts = [
                CustomPrompt(
                    text=text,
                    parameters=CustomPromptParameters(
                        model_name=self.model_name,
                        max_tokens=10,
                        temperature=0,
                    ),
                )
                for text in prompt_texts
            ]
            result_strs = self.connector.custom_multi_requests(
                prompts, progress_desc=f"Generating {eval_name}"
            )
            result_strs = [result_str.strip().lower() for result_str in result_strs]
            results = []
            for result_str in result_strs:
                if self.language == "fr":
                    if "non" in result_str:
                        result = False
                    elif "oui" in result_str:
                        result = True
                    else:
                        result = False
                elif self.language == "en":
                    if "no" in result_str:
                        result = False
                    elif "yes" in result_str:
                        result = True
                    else:
                        result = False
                else:
                    raise ValueError("Language must be 'en' or 'fr'")
                results.append(result)
            for i, result in enumerate(results):
                all_eval_results[i][eval_name] = result
        for i, eval_results in enumerate(all_eval_results):
            int_values = [int(x) for x in eval_results.values()]
            all_eval_results[i]["score"] = sum(int_values)

        evaluated_quizzes = [
            EvaluatedQuiz(quiz=quiz, evaluation=QuizEvaluation(**eval_results))
            for quiz, eval_results in zip(quizzes, all_eval_results)
        ]
        return evaluated_quizzes
