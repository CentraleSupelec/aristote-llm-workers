import warnings
from typing import List, Optional, Union

import jsonlines
from pydantic import BaseModel
from tiktoken import Encoding
from transformers import PreTrainedTokenizerBase

from quiz_generation.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
    Message,
)
from quiz_generation.dtos import Reformulation, TranscribedText
from quiz_generation.preprocessing.preprocessing import get_splits, get_token_nb
from quiz_generation.reformulation.reformulation import create_reformulations

BATCH_SIZE = 4


class MultipleAnswerQuiz(BaseModel):
    question: str  # = Field(min_length=1)
    answer: str  # = Field(min_length=1)
    fake_answer_1: str  # = Field(min_length=1)
    fake_answer_2: str  # = Field(min_length=1)
    fake_answer_3: str  # = Field(min_length=1)
    explanation: str  # = Field(min_length=1)
    max_origin_length: Optional[int] = None
    quiz_origin_text: Optional[str] = None
    origin_start: Optional[float] = None
    origin_end: Optional[float] = None


class QuizPromptsConfig(BaseModel):
    quiz_generation_prompt: str
    reformulation_prompt_path: str


class QuizGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: Union[PreTrainedTokenizerBase, Encoding],
        api_connector: AbstractConnector,
        prompts_config: QuizPromptsConfig,
        chunks_path: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.prompts_config = prompts_config
        self.chunks_path = chunks_path

        with open(prompts_config.quiz_generation_prompt, "r", encoding="utf-8") as file:
            self.quiz_generation_prompt = file.read()

    def get_custom_prompt(self, conv: List[dict]) -> CustomPrompt:
        # if isinstance(self.tokenizer, PreTrainedTokenizerBase):
        #     text = self.tokenizer.apply_chat_template(
        #         conversation=conv, tokenize=False, add_generation_prompt=True
        #     )
        #     prompt_input = CustomPrompt(
        #         text=text,
        #         parameters=CustomPromptParameters(
        #             model_name=self.model_name,
        #             max_tokens=100,
        #             temperature=0.3,
        #         ),
        #     )
        # else:
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
        transcripts: List[TranscribedText],
        max_lengths: List[int],
        # offsets: Optional[List[int]] = None,
    ) -> List[Reformulation]:
        all_transcripts: List[TranscribedText] = []
        for max_length in max_lengths:
            if len(all_transcripts) < 50:
                all_transcripts += get_splits(
                    transcripts,
                    tokenizer=self.tokenizer,
                    max_length=max_length,
                )
            else:
                warnings.warn(
                    f"Too many splits, skipping some from max length {max_length}"
                )
                break
        if self.chunks_path is not None:
            with jsonlines.open(self.chunks_path, "w") as writer:
                for chunk in all_transcripts:
                    writer.write(chunk.model_dump(mode="json"))
        all_reformulations = create_reformulations(
            all_transcripts,
            self.model_name,
            self.tokenizer,
            self.api_connector,
            self.prompts_config.reformulation_prompt_path,
        )
        return all_reformulations

    def generate_quizzes(
        self,
        reformulations: List[Reformulation],
    ) -> List[MultipleAnswerQuiz]:
        # Get Questions
        if "[EXTRACT]" not in self.quiz_generation_prompt:
            raise ValueError("Title prompt must contain [EXTRACT]")
        question_prompt = self.quiz_generation_prompt.split("{QUESTION}")[0]
        conversations = [
            [
                {
                    "role": "user",
                    "content": question_prompt.replace("[EXTRACT]", reformulation.text),
                }
            ]
            for reformulation in reformulations
        ]
        questions = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating questions",
        )
        for i, question in enumerate(questions):
            if "?" in question:
                questions[i] = question.split("?")[0]
                questions[i] += "?"

        for i, question in enumerate(questions):
            conversations[i] += [
                {"role": "assistant", "content": question},
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.split("{ANSWER}")[0].split(
                        "{QUESTION}\n"
                    )[1],
                },
            ]
        answers = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating answers",
        )
        answers = [answer + "." for answer in answers]
        for i, answer in enumerate(answers):
            if "." in answer:
                answers[i] = answer.split(".")[0]
                answers[i] += "."

        for i, answer in enumerate(answers):
            conversations[i] += [
                {"role": "assistant", "content": answer},
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.split("{FAKE ANSWER 1}")[
                        0
                    ].split("{ANSWER}\n")[1],
                },
            ]
        fake_answers_1 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 1",
        )
        fake_answers_1 = [answer + "." for answer in fake_answers_1]
        for i, answer in enumerate(fake_answers_1):
            if "." in answer:
                fake_answers_1[i] = answer.split(".")[0]
                fake_answers_1[i] += "."

        for i, fa_1 in enumerate(fake_answers_1):
            conversations[i] += [
                {"role": "assistant", "content": fa_1},
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.split("{FAKE ANSWER 2}")[
                        0
                    ].split("{FAKE ANSWER 1}\n")[1],
                },
            ]
        fake_answers_2 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 2",
        )
        fake_answers_2 = [answer + "." for answer in fake_answers_2]
        for i, answer in enumerate(fake_answers_2):
            if "." in answer:
                fake_answers_2[i] = answer.split(".")[0]
                fake_answers_2[i] += "."

        for i, fa_2 in enumerate(fake_answers_2):
            conversations[i] += [
                {"role": "assistant", "content": fa_2},
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.split("{FAKE ANSWER 3}")[
                        0
                    ].split("{FAKE ANSWER 2}\n")[1],
                },
            ]
        fake_answers_3 = self.api_connector.custom_multi_requests(
            [self.get_custom_prompt(conv) for conv in conversations],
            progress_desc="Generating fake answers 3",
        )
        fake_answers_3 = [answer + "." for answer in fake_answers_3]
        for i, answer in enumerate(fake_answers_3):
            if "." in answer:
                fake_answers_3[i] = answer.split(".")[0]
                fake_answers_3[i] += "."

        for i, fa_3 in enumerate(fake_answers_3):
            conversations[i] += [
                {"role": "assistant", "content": fa_3},
                {
                    "role": "user",
                    "content": self.quiz_generation_prompt.split("{EXPLANATION}")[
                        0
                    ].split("{FAKE ANSWER 3}\n")[1],
                },
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
                max_origin_length=get_token_nb(reformulation.text, self.tokenizer),
                quiz_origin_text=reformulation.text,
                origin_start=reformulation.start,
                origin_end=reformulation.end,
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
                reformulations,
            )
        ]

    def full_generation(
        self,
        transcripts: List[TranscribedText],
    ) -> List[MultipleAnswerQuiz]:
        max_lengths = [2000]  # , 1000, 500, 250]
        all_reformulations = self.generate_reformulations(
            transcripts,
            max_lengths,
            # offsets=[max_length // 2 for max_length in max_lengths],
        )
        quizzes = self.generate_quizzes(all_reformulations)
        return quizzes
