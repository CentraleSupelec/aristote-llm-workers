from typing import Dict, List, Optional

from pydantic import BaseModel
from transformers import AutoTokenizer

from quiz_generation.connectors.connectors import (
    AbstractConnector,
    CustomPrompt,
    CustomPromptParameters,
)
from quiz_generation.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)


class MetaData(BaseModel):
    title: str
    description: str
    discipline: Optional[str] = None
    media_type: Optional[str] = None
    main_topics: Optional[List[str]] = None


class MetadataPromptsConfig(BaseModel):
    summary_prompt_path: str
    title_prompt_path: str
    description_prompt_path: str
    generate_topics_prompt_path: str
    combine_topics_prompt_path: str
    discipline_prompt_path: Optional[str] = None
    media_type_prompt_path: Optional[str] = None


class MetadataGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        api_connector: AbstractConnector,
        prompts_config: MetadataPromptsConfig,
        debug: bool = False,
        disciplines: Optional[List[str]] = None,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.debug = debug

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
        if prompts_config.discipline_prompt_path is not None:
            with open(
                prompts_config.discipline_prompt_path, "r", encoding="utf-8"
            ) as file:
                self.discipline_prompt = file.read()
                if disciplines is not None:
                    self.discipline_prompt = self.discipline_prompt.replace(
                        "[DISCIPLINES]",
                        "\n".join([f"- {discipline}" for discipline in disciplines]),
                    )
        else:
            self.discipline_prompt = None

    def generate_summaries(
        self,
        transcripts: List[str],
    ) -> List[str]:
        # Generate summaries of reformulations
        replaced_texts = []
        if "[TRANSCRIPT]" not in self.summary_prompt:
            raise ValueError("Summary prompt must contain [TRANSCRIPT]")
        replaced_texts = [
            self.summary_prompt.replace("[TRANSCRIPT]", transcript)
            for transcript in transcripts
        ]
        templated_transcripts = [
            get_templated_script(text, self.tokenizer) for text in replaced_texts
        ]
        summaries = self.api_connector.custom_multi_requests(
            prompts=[
                CustomPrompt(
                    text=templated_transcript,
                    parameters=CustomPromptParameters(
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
        )
        summaries = [summary.replace("\n\n", "\n") for summary in summaries]
        return summaries

    def generate_main_elements(
        self,
        summaries: List[str],
    ) -> Dict[str, str]:
        """Generate description, title and discipline category
        from title and description.

        Args:
            summaries (List[str]): Summaries of different transcripts

        Returns:
            Dict[str, str]: _description_
        """
        full_summary = "\n".join(summaries)
        if "[SUMMARIES]" not in self.description_prompt:
            raise ValueError("Prompt must contain [SUMMARIES]")

        # Description generation
        description_instruction = self.description_prompt.replace(
            "[SUMMARIES]", full_summary
        )
        description_prompt = get_templated_script(
            description_instruction, self.tokenizer
        )
        if self.debug:
            print("Description prompt: ", description_prompt)
            print("Desc Tokens: ", get_token_nb(description_prompt, self.tokenizer))
            print("============================================================")
        description = self.api_connector.generate(
            CustomPrompt(
                text=description_prompt,
                parameters=CustomPromptParameters(
                    model_name=self.model_name,
                    max_tokens=500,
                    temperature=0.1,
                ),
            ),
        )
        if self.debug:
            print("Description:", description)
            print("============================================================")

        # Title generation
        if "[SUMMARIES]" not in self.title_prompt:
            raise ValueError("Title prompt must contain [SUMMARIES]")
        title_instruction = self.title_prompt.replace("[SUMMARIES]", full_summary)
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
            print("Title:", title)
            print("============================================================")

        # Discipline generation
        if (
            "[TITLE]" not in self.discipline_prompt
            or "[DESCRIPTION]" not in self.discipline_prompt
        ):
            raise ValueError("Discipline prompt must contain [TITLE], [DESCRIPTION]")
        discipline_instruction = self.discipline_prompt.replace(
            "[TITLE]", title
        ).replace("[DESCRIPTION]", description)
        discipline_prompt = get_templated_script(discipline_instruction, self.tokenizer)
        if self.debug:
            print("Title prompt:", discipline_prompt)
            print("Title Tokens: ", get_token_nb(discipline_prompt, self.tokenizer))
            print("============================================================")
        discipline = self.api_connector.generate(
            CustomPrompt(
                text=discipline_prompt,
                parameters=CustomPromptParameters(
                    model_name=self.model_name,
                    max_tokens=100,
                    temperature=0.1,
                    stop=["\n", "."],
                ),
            ),
        )
        if self.debug:
            print("Discipline:", discipline)
            print("============================================================")

        return {
            "title": title,
            "description": description,
            "discipline": discipline,
        }

    def generate_main_topics(self, summaries: List[str]) -> List[str]:
        # Topics generation
        full_summary = "\n".join(summaries)
        if "[SUMMARIES]" not in self.generate_topics_prompt:
            raise ValueError("Topic generation prompt must contain [SUMMARIES]")
        topics_instruction = self.generate_topics_prompt.replace(
            "[SUMMARIES]", full_summary
        )
        topics_prompt = get_templated_script(topics_instruction, self.tokenizer)
        if self.debug:
            print("Topics generation prompt:", topics_prompt)
            print(
                "Topics generation tokens: ",
                get_token_nb(topics_prompt, self.tokenizer),
            )
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
        topics_list = [topic for topic in topics_list_raw.split("\n-")]
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
            print("Topics:", topics_list)
            print("============================================================")
        return topics_list

    def generate_metadata(
        self,
        transcripts: List[str],
    ) -> MetaData:
        # Generate summaries
        summaries = self.generate_summaries(transcripts)
        if self.debug:
            print("Summaries:", summaries)
            print("============================================================")

        # Generate simple metadata
        partial_metadata = self.generate_main_elements(summaries)

        topics = self.generate_main_topics(summaries)

        return MetaData(
            title=partial_metadata["title"],
            description=partial_metadata["description"],
            discipline=partial_metadata["discipline"],
            main_topics=topics,
        )
