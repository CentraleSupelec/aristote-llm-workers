from typing import List, Optional, Tuple

from pydantic import BaseModel
from transformers import AutoTokenizer

from quiz_generation.connectors.api_connector import APIConnector, Prompt
from quiz_generation.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)


class MetaData(BaseModel):
    title: str
    description: str
    main_topics: Optional[List[str]] = None


class MetadataPromptsConfig(BaseModel):
    summary_prompt_path: str
    title_prompt_path: str
    description_prompt_path: str
    generate_topics_prompt_path: str
    combine_topics_prompt_path: str


class MetadataGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        api_connector: APIConnector,
        prompts_config: MetadataPromptsConfig,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector

        with open(prompts_config.summary_prompt_path, "r", encoding="utf-8") as file:
            self.summary_prompt = file.read()
        with open(prompts_config.title_prompt_path, "r", encoding="utf-8") as file:
            self.title_prompt = file.read()
        with open(
            prompts_config.description_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.description_prompt = file.read()
        with open(
            prompts_config.generate_topics_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.generate_topics_prompt = file.read()
        with open(
            prompts_config.combine_topics_prompt_path, "r", encoding="utf-8"
        ) as file:
            self.combine_topics_prompt = file.read()

    def generate_summaries(
        self,
        transcripts: List[str],
    ) -> List[str]:
        # Generate summaries of reformulations
        replaced_texts = [
            self.summary_prompt.replace("[TRANSCRIPT]", transcript)
            for transcript in transcripts
        ]
        templated_transcripts = [
            get_templated_script(text, self.tokenizer) for text in replaced_texts
        ]
        summaries = self.api_connector.multi_requests(
            prompts=[
                Prompt(
                    text=templated_transcript,
                    model_name=self.model_name,
                    max_tokens=get_token_nb(templated_transcript, self.tokenizer),
                    temperature=0.1,
                    stop=["\n"],
                )
                for templated_transcript in templated_transcripts
            ],
            description="Generating summaries",
        )
        summaries = [summary.replace("\n\n", "\n") for summary in summaries]
        return summaries

    def generate_description_and_title(
        self,
        summaries: List[str],
    ) -> Tuple[str, str]:
        full_summary = "\n".join(summaries)
        description_instruction = self.description_prompt.replace(
            "[SUMMARIES]", full_summary
        )
        description = self.api_connector.generate(
            Prompt(
                text=get_templated_script(description_instruction, self.tokenizer),
                model_name=self.model_name,
                max_tokens=500,
                temperature=0.1,
            ),
        )
        title_instruction = self.title_prompt.replace("[SUMMARIES]", full_summary)
        title = self.api_connector.generate(
            Prompt(
                text=get_templated_script(title_instruction, self.tokenizer),
                model_name=self.model_name,
                max_tokens=30,
                temperature=0,
                stop=["\n", "."],
            ),
        )
        return description, title

    def generate_main_topics(self, transcripts: List[str]) -> List[str]:
        raise NotImplementedError()

    def generate_metadata(
        self,
        transcripts: List[str],
    ) -> MetaData:
        # Generate summaries
        summaries = self.generate_summaries(transcripts)

        # Generate description
        description, title = self.generate_description_and_title(summaries)

        # Generate main topics
        main_topics: List[str] = []  # self.generate_main_topics(summaries)

        return MetaData(
            title=title,
            description=description,
            main_topics=main_topics,
        )
