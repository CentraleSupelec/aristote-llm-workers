import warnings
from typing import Dict, List, Optional

from pydantic import BaseModel
from transformers import AutoTokenizer

from aristote.connectors.connectors import (
    AbstractConnector,
    Prompt,
    PromptParameters,
)
from aristote.dtos.dtos import MediaType, MetaData, Reformulation, Summary
from aristote.preprocessing.preprocessing import (
    get_templated_script,
    get_token_nb,
)


class MetadataPromptsConfig(BaseModel):
    reformulation_prompt_path: str
    summary_prompt_path: str
    title_prompt_path: str
    description_prompt_path: str
    generate_topics_prompt_path: str
    discipline_prompt_path: Optional[str] = None
    media_type_prompt_path: Optional[str] = None
    local_media_type_prompt_path: Optional[str] = None


class MetadataGenerator:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        api_connector: AbstractConnector,
        prompts_config: MetadataPromptsConfig,
        debug: bool = False,
        disciplines: Optional[List[str]] = None,
        media_types: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
    ) -> None:
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.api_connector = api_connector
        self.debug = debug
        self.batch_size = batch_size
        self.media_types = media_types
        self.disciplines = disciplines

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
                    warnings.warn("No disciplines provided, using empty string")
                    self.discipline_prompt = self.discipline_prompt.replace(
                        "[DISCIPLINES]", ""
                    )
        else:
            warnings.warn(
                "No discipline_prompt provided, discipline will not be categorised"
            )
            self.discipline_prompt = None

        if prompts_config.local_media_type_prompt_path is not None:
            with open(
                prompts_config.local_media_type_prompt_path, "r", encoding="utf-8"
            ) as file:
                self.local_media_type_prompt = file.read()
                if media_types is not None:
                    self.local_media_type_prompt = self.local_media_type_prompt.replace(
                        "[MEDIA_TYPES]",
                        "\n".join([f"- {media_type}" for media_type in media_types]),
                    )
                else:
                    warnings.warn("No media types provided, using empty string")
                    self.discipline_prompt = self.discipline_prompt.replace(
                        "[MEDIA_TYPES]", ""
                    )
        else:
            warnings.warn(
                "No local_media_type_prompt provided, local media type"
                + " will not be categorised"
            )
            self.local_media_type_prompt = None

        if prompts_config.media_type_prompt_path is not None:
            with open(
                prompts_config.media_type_prompt_path, "r", encoding="utf-8"
            ) as file:
                self.media_type_prompt = file.read()
                if media_types is not None:
                    self.media_type_prompt = self.media_type_prompt.replace(
                        "[MEDIA_TYPES]",
                        "\n".join([f"- {media_type}" for media_type in media_types]),
                    )
                else:
                    warnings.warn("No media types provided, using empty string")
                    self.media_type_prompt = self.media_type_prompt.replace(
                        "[MEDIA_TYPES]", ""
                    )
        else:
            warnings.warn(
                "No media_type_prompt provided, media type will not be categorised"
            )
            self.media_type_prompt = None

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

    def generate_local_media_types(
        self,
        transcripts: List[Reformulation],
    ) -> List[MediaType]:
        if self.media_types is not None and len(self.media_types) == 1:
            return [
                MediaType(
                    text=self.media_types[0],
                    start=transcripts[0].start,
                    end=transcripts[len(transcripts) - 1].end,
                )
            ]

        # Generate media type of reformulations
        replaced_texts = []
        if "[TRANSCRIPT]" not in self.local_media_type_prompt:
            raise ValueError("Local media type prompt must contain [TRANSCRIPT]")
        replaced_texts = [
            self.local_media_type_prompt.replace("[TRANSCRIPT]", transcript.text)
            for transcript in transcripts
        ]
        templated_transcripts = [
            get_templated_script(text, self.tokenizer) for text in replaced_texts
        ]
        local_media_types_text = self.api_connector.custom_multi_requests(
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
            progress_desc="Generating local media types",
            batch_size=self.batch_size,
        )
        local_media_types = [
            MediaType(
                text=local_media_type_text.replace("\n\n", "\n"),
                start=transcript.start,
                end=transcript.end,
            )
            for local_media_type_text, transcript in zip(
                local_media_types_text, transcripts
            )
        ]
        return local_media_types

    def generate_main_elements(
        self, summaries: List[Summary], local_media_types: List[MediaType]
    ) -> Dict[str, str]:
        """Generate description, title and discipline category
        from title and description.

        Args:
            summaries (List[str]): Summaries of different transcripts

        Returns:
            Dict[str, str]: _description_
        """
        full_summary = "\n".join([summary.text for summary in summaries])
        if "[SUMMARIES]" not in self.description_prompt:
            raise ValueError("Prompt must contain [SUMMARIES]")

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
            Prompt(
                text=title_prompt,
                parameters=PromptParameters(
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

        # Media type generation
        if self.media_types is not None and len(self.media_types) == 1:
            media_type = self.media_types[0]
        elif self.media_type_prompt is None:
            media_type = None
        else:
            if (
                "[TITLE]" not in self.media_type_prompt
                or "[LOCAL_MEDIA_TYPES]" not in self.media_type_prompt
            ):
                raise ValueError(
                    "Media type prompt must contain [TITLE] and [LOCAL_MEIDA_TYPES]"
                )
            media_type_instruction = self.media_type_prompt.replace(
                "[TITLE]", title
            ).replace(
                "[LOCAL_MEDIA_TYPES]",
                "\n".join(
                    [
                        f"- {local_media_type.text}"
                        for local_media_type in local_media_types
                    ]
                ),
            )
            media_type_prompt = get_templated_script(
                media_type_instruction, self.tokenizer
            )
            if self.debug:
                print("Media type prompt:", media_type_prompt)
                print(
                    "Media type Tokens: ",
                    get_token_nb(media_type_prompt, self.tokenizer),
                )
                print("============================================================")
            media_type = self.api_connector.generate(
                Prompt(
                    text=media_type_prompt,
                    parameters=PromptParameters(
                        model_name=self.model_name,
                        max_tokens=100,
                        temperature=0.1,
                        stop=["\n", "."],
                    ),
                ),
            )
        if self.debug:
            print("Media type:", media_type)
            print("============================================================")

        # Description generation
        description_instruction = self.description_prompt.replace(
            "[SUMMARIES]", full_summary
        ).replace("[MEDIA_TYPE]", media_type)
        description_prompt = get_templated_script(
            description_instruction, self.tokenizer
        )
        if self.debug:
            print("Description prompt: ", description_prompt)
            print("Desc Tokens: ", get_token_nb(description_prompt, self.tokenizer))
            print("============================================================")
        description = self.api_connector.generate(
            Prompt(
                text=description_prompt,
                parameters=PromptParameters(
                    model_name=self.model_name,
                    max_tokens=500,
                    temperature=0.1,
                ),
            ),
        )
        if self.debug:
            print("Description:", description)
            print("============================================================")

        # Discipline generation
        if self.discipline_prompt is None:
            discipline = None
        else:
            if (
                "[TITLE]" not in self.discipline_prompt
                or "[DESCRIPTION]" not in self.discipline_prompt
            ):
                raise ValueError(
                    "Discipline prompt must contain [TITLE], [DESCRIPTION]"
                )
            discipline_instruction = self.discipline_prompt.replace(
                "[TITLE]", title
            ).replace("[DESCRIPTION]", description)
            discipline_prompt = get_templated_script(
                discipline_instruction, self.tokenizer
            )
            if self.debug:
                print("Discipline prompt:", discipline_prompt)
                print(
                    "Discipline Tokens: ",
                    get_token_nb(discipline_prompt, self.tokenizer),
                )
                print("============================================================")
            discipline = self.api_connector.generate(
                Prompt(
                    text=discipline_prompt,
                    parameters=PromptParameters(
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
            "discipline": discipline.strip(),
            "media_type": media_type.strip(),
        }

    def generate_main_topics(self, summaries: List[Summary]) -> List[str]:
        # Topics generation
        full_summary = "\n".join([summary.text for summary in summaries])
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
            Prompt(
                text=topics_prompt,
                parameters=PromptParameters(
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
            print("Topics:", topics_list)
            print("============================================================")
        return topics_list

    def generate_metadata(
        self,
        transcripts: List[Reformulation],
    ) -> MetaData:
        # Generate summaries
        summaries = self.generate_summaries(transcripts)
        local_media_types = self.generate_local_media_types(transcripts)
        if self.debug:
            print("Summaries:", summaries)
            print("============================================================")

        # Generate simple metadata
        partial_metadata = self.generate_main_elements(summaries, local_media_types)

        topics = self.generate_main_topics(summaries)

        return MetaData(
            title=partial_metadata["title"],
            description=partial_metadata["description"],
            discipline=partial_metadata["discipline"],
            media_type=partial_metadata["media_type"],
            main_topics=topics,
        )
