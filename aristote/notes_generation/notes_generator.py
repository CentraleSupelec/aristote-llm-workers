from typing import List, Optional

from pydantic import BaseModel
from transformers import AutoTokenizer

from aristote.connectors.connectors import (
    AbstractConnector,
    Prompt,
    PromptParameters,
)
from aristote.dtos.dtos import Reformulation, Summary
from aristote.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)


class NotesPromptsConfig(BaseModel):
    notes_prompt_path: str
    reformulation_prompt_path: str
    summary_prompt_path: str


class NotesGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        api_connector: AbstractConnector,
        prompts_config: NotesPromptsConfig,
        debug: bool = False,
        start_timestamp: str = None,
        end_timestamp: str = None,
        batch_size: Optional[int] = None,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.debug = debug
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.batch_size = batch_size

        with open(prompts_config.notes_prompt_path, "r", encoding="utf-8") as file:
            self.notes_prompt = file.read()
        with open(prompts_config.summary_prompt_path, "r", encoding="utf-8") as file:
            self.summary_prompt = file.read()

    def generate_summaries(
        self,
        transcripts: List[Reformulation],
    ) -> List[Summary]:
        # Generate summaries of reformulations
        replaced_texts = []
        if "[TRANSCRIPT]" not in self.summary_prompt:
            raise ValueError("Summary prompt must contain [TRANSCRIPT]")
        replaced_texts = [
            self.summary_prompt.replace("[TRANSCRIPT]", transcript.text)
            for transcript in transcripts
        ]
        templated_transcripts = [
            get_templated_script(text, self.tokenizer) for text in replaced_texts
        ]
        summary_texts = self.api_connector.custom_multi_requests(
            prompts=[
                Prompt(
                    text=templated_transcript,
                    parameters=PromptParameters(
                        model_name=self.model_name,
                        max_tokens=min(
                            3500 // len(templated_transcripts),
                            get_token_nb(templated_transcript, self.tokenizer),
                        ),
                        temperature=0.1,
                        stop=["\n"],
                    ),
                )
                for templated_transcript in templated_transcripts
            ],
            progress_desc="Generating summaries",
            batch_size=self.batch_size,
        )
        summaries = [
            Summary(
                text=summary_text.replace("\n\n", "\n"),
                start=transcript.start,
                end=transcript.end,
            )
            for summary_text, transcript in zip(summary_texts, transcripts)
        ]
        return summaries

    def generate_notes_from_summaries(
        self, summaries: List[Summary], start_timestamp: str, end_timestamp: str
    ) -> str:
        """Generate notes

        Args:
            summaries (List[str]): Summaries of different transcripts

        Returns:
            str: _notes_
        """
        full_summary = "\n".join([summary.text for summary in summaries])
        if "[SUMMARIES]" not in self.notes_prompt:
            raise ValueError("Prompt must contain [SUMMARIES]")

        if "[DURATION]" not in self.notes_prompt:
            raise ValueError("Prompt must contain [DURATION]")

        # Notes generation
        notes_instruction = self.notes_prompt.replace(
            "[SUMMARIES]", full_summary
        ).replace("[DURATION]", str(int(float(end_timestamp) - float(start_timestamp))))
        notes_prompt = get_templated_script(notes_instruction, self.tokenizer)

        if self.debug:
            print("Notes prompt: ", notes_prompt)
            print("Desc Tokens: ", get_token_nb(notes_prompt, self.tokenizer))
            print("============================================================")
        notes = self.api_connector.generate(
            Prompt(
                text=notes_prompt,
                parameters=PromptParameters(
                    model_name=self.model_name,
                    max_tokens=1000,
                    temperature=0.1,
                ),
            ),
        )
        if self.debug:
            print("Notes:", notes)
            print("============================================================")

        return notes

    def generate_notes(
        self,
        transcripts: List[Reformulation],
    ) -> str:
        summaries = self.generate_summaries(transcripts)
        notes = self.generate_notes_from_summaries(
            summaries, self.start_timestamp, self.end_timestamp
        )

        return notes
