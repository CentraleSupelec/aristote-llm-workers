import warnings
from typing import List, Optional

from pydantic import BaseModel
from transformers import AutoTokenizer

from aristote.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
    Message,
)
from aristote.dtos.dtos import MetaData, TranscribedText
from aristote.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)
from aristote.quiz_generation.quiz_generator import MultipleAnswerQuiz


class TranslationPromptsConfig(BaseModel):
    quiz_translation_prompt_path: str
    transcript_translation_prompt_path: str
    title_translation_prompt_path: str
    description_translation_prompt_path: str
    topics_translation_prompt_path: str
    notes_translation_prompt_path: str


class TranslationResult(BaseModel):
    meta_data: Optional[MetaData] = None
    quizzes: List[MultipleAnswerQuiz]
    transcript: List[TranscribedText]
    notes: Optional[str] = None


class TranslationGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        api_connector: AbstractConnector,
        prompts_config: TranslationPromptsConfig,
        debug: bool = False,
        topics: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.debug = debug
        self.batch_size = batch_size

        with open(
            prompts_config.title_translation_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.title_prompt = file.read()
        with open(
            prompts_config.description_translation_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.description_prompt = file.read()
        with open(
            prompts_config.quiz_translation_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.quiz_translation_prompt = file.read()
        with open(
            prompts_config.transcript_translation_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.transcript_translation_prompt = file.read()

        with open(
            prompts_config.notes_translation_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.notes_prompt = file.read()

        if prompts_config.topics_translation_prompt_path is not None:
            with open(
                prompts_config.topics_translation_prompt_path, "r", encoding="utf-8"
            ) as file:
                self.topics_prompt = file.read()
                if topics is not None:
                    self.topics_prompt = self.topics_prompt.replace(
                        "[TOPICS]",
                        "\n".join([f"- {topic}" for topic in topics]),
                    )
                else:
                    warnings.warn("No topics provided, using empty string")
                    self.topics_prompt = self.topics_prompt.replace("[TOPICS]", "")
        else:
            warnings.warn("No topics_prompt provided, topics will not be translated")
            self.topics_prompt = None

    def get_custom_prompt(self, conv: List[dict]) -> CustomPrompt:
        prompt_input = CustomPrompt(
            messages=[Message(**message) for message in conv],
            parameters=CustomPromptParameters(
                model_name=self.model_name,
                max_tokens=1000,
                temperature=0,
            ),
        )
        return prompt_input

    def generate_metadata_translation(
        self, meta_data: MetaData, from_language: str, to_language: str
    ) -> MetaData:
        # Generate metadata translation

        if meta_data is None:
            return None

        if self.title_prompt is None:
            title = None
        else:
            if (
                "[TITLE]" not in self.title_prompt
                or "[FROM_LANGUAGE]" not in self.title_prompt
                or "[TO_LANGUAGE]" not in self.title_prompt
            ):
                raise ValueError(
                    "Title prompt must contain [TITLE], [FROM_LANGUAGE]"
                    + " and [TO_LANGUAGE]"
                )
            title_instruction = (
                self.title_prompt.replace("[TITLE]", meta_data.title)
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
            )

            title_prompt = get_templated_script(title_instruction, self.tokenizer)
            if self.debug:
                print("Title prompt:", title_prompt)
                print("Title Tokens: ", get_token_nb(title_prompt, self.tokenizer))
                print("============================================================")
            title = self.api_connector.generate(
                CustomPrompt(
                    text=title_prompt,
                    parameters=CustomPromptParameters(
                        model_name=self.model_name,
                        max_tokens=100,
                        temperature=0.1,
                        stop=["\n", "."],
                    ),
                ),
            )
        if self.debug:
            print("Titre:", title)
            print("============================================================")

        if self.description_prompt is None:
            description = None
        else:
            if (
                "[DESCRIPTION]" not in self.description_prompt
                or "[FROM_LANGUAGE]" not in self.description_prompt
                or "[TO_LANGUAGE]" not in self.description_prompt
            ):
                raise ValueError(
                    "Description prompt must contain [TITLE], "
                    + "[FROM_LANGUAGE] and [TO_LANGUAGE]"
                )
            description_instruction = (
                self.description_prompt.replace("[DESCRIPTION]", meta_data.description)
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
            )

            description_prompt = get_templated_script(
                description_instruction, self.tokenizer
            )
            if self.debug:
                print("Description prompt:", description_prompt)
                print(
                    "Description Tokens: ",
                    get_token_nb(description_prompt, self.tokenizer),
                )
                print("============================================================")
            description = self.api_connector.generate(
                CustomPrompt(
                    text=description_prompt,
                    parameters=CustomPromptParameters(
                        model_name=self.model_name,
                        max_tokens=100,
                        temperature=0.1,
                        stop=["\n", "."],
                    ),
                ),
            )
        if self.debug:
            print("Description:", description)
            print("============================================================")

        # Topics translation
        if self.topics_prompt is None:
            topics_list = None
        else:
            if (
                "[TITLE]" not in self.topics_prompt
                or "[DESCRIPTION]" not in self.topics_prompt
                or "[FROM_LANGUAGE]" not in self.description_prompt
                or "[TO_LANGUAGE]" not in self.description_prompt
            ):
                raise ValueError("Topics prompt must contain [TITLE], [DESCRIPTION]")
            topics_instruction = (
                self.topics_prompt.replace("[TITLE]", meta_data.title)
                .replace("[DESCRIPTION]", meta_data.description)
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
            )

            topics_prompt = get_templated_script(topics_instruction, self.tokenizer)
            if self.debug:
                print("Topics prompt:", topics_prompt)
                print("Topics Tokens: ", get_token_nb(topics_prompt, self.tokenizer))
                print("============================================================")
            topics_list_raw = self.api_connector.generate(
                CustomPrompt(
                    text=topics_prompt,
                    parameters=CustomPromptParameters(
                        model_name=self.model_name,
                        max_tokens=512,
                        temperature=0.1,
                    ),
                ),
            )

            topics_list = [
                topic for topic in topics_list_raw.split("\n-") if ":" not in topic
            ]
            if len(topics_list) == 1:
                topics_list = topics_list[0].split("\n")
            if len(topics_list) == 1:
                topics_list = topics_list[0].split("- ")
            topics_list = list(
                filter(
                    lambda topic: "SUJET" not in topic and len(topic.strip()) > 0,
                    [topic.strip() for topic in topics_list],
                )
            )
            if self.debug:
                print("Topics Raw:\n", topics_list_raw)

                print("Topics:", topics_list)
                print("============================================================")

        return MetaData(title=title, description=description, main_topics=topics_list)

    def generate_notes_translation(
        self, notes: str, from_language: str, to_language: str
    ) -> str:
        if notes is None:
            return None

        if self.notes_prompt is None:
            translated_notes = None
        else:
            if (
                "[NOTES]" not in self.notes_prompt
                or "[FROM_LANGUAGE]" not in self.notes_prompt
                or "[TO_LANGUAGE]" not in self.notes_prompt
            ):
                raise ValueError(
                    "Notes prompt must contain [NOTES], [FROM_LANGUAGE]"
                    + " and [TO_LANGUAGE]"
                )
            notes_instruction = (
                self.notes_prompt.replace("[NOTES]", notes)
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
            )

            notes_prompt = get_templated_script(notes_instruction, self.tokenizer)
            if self.debug:
                print("Notes prompt:", notes_prompt)
                print("Notes Tokens: ", get_token_nb(notes_prompt, self.tokenizer))
                print("============================================================")
            translated_notes = self.api_connector.generate(
                CustomPrompt(
                    text=notes_prompt,
                    parameters=CustomPromptParameters(
                        model_name=self.model_name,
                        max_tokens=500,
                        temperature=0.1,
                    ),
                ),
            )
        if self.debug:
            print("Notes:", translated_notes)
            print("============================================================")

        return translated_notes

    def generate_quizzes_translation(
        self,
        meta_data: MetaData,
        quizzes: List[MultipleAnswerQuiz],
        from_language: str,
        to_language: str,
    ) -> List[MultipleAnswerQuiz]:

        if self.quiz_translation_prompt is None:
            return
        else:
            if (
                "[TITLE]" not in self.quiz_translation_prompt
                or "[DESCRIPTION]" not in self.quiz_translation_prompt
                or "[FROM_LANGUAGE]" not in self.quiz_translation_prompt
                or "[TO_LANGUAGE]" not in self.quiz_translation_prompt
            ):
                raise ValueError(
                    "Quiz Translation prompt prompt must contain [TITLE], "
                    + "[DESCRIPTION], [FROM_LANGUAGE] and [TO_LANGUAGE]"
                )

            question_prompt = (
                self.quiz_translation_prompt.replace(
                    "[TITLE]", meta_data.title if meta_data is not None else "N/A"
                )
                .replace(
                    "[DESCRIPTION]",
                    meta_data.description if meta_data is not None else "N/A",
                )
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
                .split("{TRANSLATED_QUESTION}")[0]
            )
            conversations = [
                [
                    {
                        "role": "user",
                        "content": question_prompt.replace("{QUESTION}", quiz.question),
                    }
                ]
                for quiz in quizzes
            ]
            questions = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating questions",
                batch_size=self.batch_size,
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
                        "content": self.quiz_translation_prompt.replace(
                            "{ANSWER}", quizzes[i].answer
                        )
                        .split("{TRANSLATED_ANSWER}")[0]
                        .split("{TRANSLATED_QUESTION}\n")[1],
                    },
                ]
            answers = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating answers",
                batch_size=self.batch_size,
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
                        "content": self.quiz_translation_prompt.replace(
                            "{FAKE_ANSWER_1}", quizzes[i].fake_answer_1
                        )
                        .split("{TRANSLATED_FAKE_ANSWER_1}")[0]
                        .split("{TRANSLATED_ANSWER}\n")[1],
                    },
                ]

            fake_answers_1 = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating fake answers 1",
                batch_size=self.batch_size,
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
                        "content": self.quiz_translation_prompt.replace(
                            "{FAKE_ANSWER_2}", quizzes[i].fake_answer_2
                        )
                        .split("{TRANSLATED_FAKE_ANSWER_2}")[0]
                        .split("{TRANSLATED_FAKE_ANSWER_1}\n")[1],
                    },
                ]
            fake_answers_2 = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating fake answers 2",
                batch_size=self.batch_size,
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
                        "content": self.quiz_translation_prompt.replace(
                            "{FAKE_ANSWER_3}", quizzes[i].fake_answer_3
                        )
                        .split("{TRANSLATED_FAKE_ANSWER_3}")[0]
                        .split("{TRANSLATED_FAKE_ANSWER_2}\n")[1],
                    },
                ]
            fake_answers_3 = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating fake answers 3",
                batch_size=self.batch_size,
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
                        "content": self.quiz_translation_prompt.replace(
                            "{EXPLANATION}", quizzes[i].explanation
                        )
                        .split("{TRANSLATED_EXPLANATION}")[0]
                        .split("{TRANSLATED_FAKE_ANSWER_3}\n")[1],
                    },
                ]
            explanations = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating explanations",
                batch_size=self.batch_size,
            )

        return [
            MultipleAnswerQuiz(
                question=question,
                answer=answer,
                fake_answer_1=fake_answer_1,
                fake_answer_2=fake_answer_2,
                fake_answer_3=fake_answer_3,
                explanation=explanation,
            )
            for (
                question,
                answer,
                fake_answer_1,
                fake_answer_2,
                fake_answer_3,
                explanation,
            ) in zip(
                questions,
                answers,
                fake_answers_1,
                fake_answers_2,
                fake_answers_3,
                explanations,
            )
        ]

    def generate_transcript_translation(
        self,
        meta_data: MetaData,
        transcripts: List[TranscribedText],
        from_language: str,
        to_language: str,
    ) -> List[TranscribedText]:

        if self.transcript_translation_prompt is None:
            return
        else:
            if (
                "[TITLE]" not in self.transcript_translation_prompt
                or "[DESCRIPTION]" not in self.transcript_translation_prompt
                or "[FROM_LANGUAGE]" not in self.transcript_translation_prompt
                or "[TO_LANGUAGE]" not in self.transcript_translation_prompt
            ):
                raise ValueError(
                    "Quiz Translation prompt prompt must contain [TITLE], "
                    + "[DESCRIPTION], [FROM_LANGUAGE] and [TO_LANGUAGE]"
                )

            transcript_translation_prompt = (
                self.transcript_translation_prompt.replace(
                    "[TITLE]", meta_data.title if meta_data is not None else "N/A"
                )
                .replace(
                    "[DESCRIPTION]",
                    meta_data.description if meta_data is not None else "N/A",
                )
                .replace("[FROM_LANGUAGE]", from_language)
                .replace("[TO_LANGUAGE]", to_language)
                .split("{TRANSLATED_TEXT}")[0]
            )
            conversations = [
                [
                    {
                        "role": "user",
                        "content": transcript_translation_prompt.replace(
                            "{TEXT}", transcript.text
                        ),
                    }
                ]
                for transcript in transcripts
            ]
            translated_transcripts = self.api_connector.custom_multi_requests(
                [self.get_custom_prompt(conv) for conv in conversations],
                progress_desc="Translating transcript",
                batch_size=self.batch_size,
            )

        return [
            TranscribedText(
                text=translated_transcript,
                start=transcripts[i].start,
                end=transcripts[i].end,
            )
            for i, translated_transcript in enumerate(translated_transcripts)
        ]

    def generate_translation(
        self,
        meta_data: MetaData,
        transcripts: List[TranscribedText],
        quizzes: List[MultipleAnswerQuiz],
        notes: str,
        from_language: str,
        to_language: str,
    ) -> TranslationResult:
        meta_data_translation = self.generate_metadata_translation(
            meta_data=meta_data, from_language=from_language, to_language=to_language
        )
        quizzes_translation = self.generate_quizzes_translation(
            meta_data=meta_data,
            quizzes=quizzes,
            from_language=from_language,
            to_language=to_language,
        )
        transcripts_translation = self.generate_transcript_translation(
            meta_data=meta_data,
            transcripts=transcripts,
            from_language=from_language,
            to_language=to_language,
        )
        notes_translation = self.generate_notes_translation(
            notes=notes,
            from_language=from_language,
            to_language=to_language,
        )

        return TranslationResult(
            meta_data=meta_data_translation,
            quizzes=quizzes_translation,
            transcript=transcripts_translation,
            notes=notes_translation,
        )
