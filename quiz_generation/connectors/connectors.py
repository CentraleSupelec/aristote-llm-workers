import hashlib
import warnings
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import requests
from diskcache import Cache
from illuin_llm_tools import (
    Message,
    OpenAIConnector,
    Prompt,
    PromptParameters,
    TextGeneration,
)
from pydantic import BaseModel
from tqdm import tqdm


class CustomPromptParameters(BaseModel):
    model_name: str
    max_tokens: int = 256
    temperature: float = 0.5
    stop: Optional[List[str]] = None


class CustomPrompt(BaseModel):
    text: Optional[str] = None
    messages: Optional[List[Message]] = None
    parameters: CustomPromptParameters


class AbstractConnector:
    def __init__(self, cache_path: Optional[str] = None) -> None:
        self.cache_path = cache_path

    @abstractmethod
    def generate(self, prompt: CustomPrompt) -> str:
        pass

    @abstractmethod
    def custom_multi_requests(
        self, prompts: List[CustomPrompt], progress_desc: str
    ) -> List[str]:
        pass


class CustomOpenAIConnector(OpenAIConnector, AbstractConnector):
    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        backoff_max_time: int = 30,
        request_timeout: Optional[int] = None,
        cache_path: Optional[str] = None,
        verbosity: int = 1,
        max_requests_per_second: float = 1.0,
    ):
        OpenAIConnector.__init__(
            self,
            api_key,
            organization,
            backoff_max_time,
            request_timeout,
            cache_path,
            verbosity,
        )
        AbstractConnector.__init__(self, cache_path=cache_path)
        self.max_requests_per_second = max_requests_per_second

    def generate(self, prompt: CustomPrompt) -> str:
        text_generation = self.make_request(
            prompt=Prompt(
                text=prompt.text,
                messages=prompt.messages,
                parameters=PromptParameters(
                    model=prompt.parameters.model_name,
                    max_tokens=prompt.parameters.max_tokens,
                    temperature=prompt.parameters.temperature,
                    stop=prompt.parameters.stop,
                ),
            )
        )
        if isinstance(text_generation, TextGeneration):
            if isinstance(text_generation.text, str):
                return text_generation.text
            else:
                raise ValueError("Text generation failed")
        else:
            raise ValueError("Wrong generation type")

    def custom_multi_requests(
        self, prompts: List[CustomPrompt], progress_desc: str
    ) -> List[str]:
        llm_tools_prompts = [
            Prompt(
                text=prompt.text,
                messages=prompt.messages,
                parameters=PromptParameters(
                    model=prompt.parameters.model_name,
                    max_tokens=prompt.parameters.max_tokens,
                    temperature=prompt.parameters.temperature,
                    stop=prompt.parameters.stop,
                ),
            )
            for prompt in prompts
        ]
        print("Cost: ", self.get_costs(llm_tools_prompts))
        results = self.multi_requests(
            llm_tools_prompts,
            max_requests_per_second=self.max_requests_per_second,
            progress_desc=progress_desc,
        )
        return [result.text for result in results]


def get_cache_key(prompt: CustomPrompt) -> str:
    if prompt.parameters.stop is not None:
        stop_str = "-".join(prompt.parameters.stop)
    else:
        stop_str = ""
    if prompt.messages is not None:
        messages_str = "-".join(
            [f"{message.role}-{message.content}" for message in prompt.messages]
        )
    else:
        messages_str = ""
    str_to_encode = (
        f"{prompt.parameters.model_name}-"
        f"{prompt.parameters.max_tokens}-"
        f"{prompt.parameters.temperature}-"
        f"{stop_str}-"
        f"{prompt.text}-"
        f"{messages_str}"
    )
    return str(hashlib.sha256(str_to_encode.encode()).hexdigest())


class APIConnector(AbstractConnector):
    def __init__(self, api_url: str, cache_path: str) -> None:
        self.api_url = api_url
        self.cache = Cache(cache_path)

    def generate(
        self,
        prompt: CustomPrompt,
    ) -> str:
        cache_key = get_cache_key(prompt)
        cached_text = self.cache.get(cache_key)
        if isinstance(cached_text, str):
            return cached_text
        else:
            try:
                if prompt.text is None and prompt.messages is None:
                    raise ValueError("Prompt must contain text or messages")
                else:
                    if prompt.messages is not None:
                        json_load = {
                            "messages": [
                                message.model_dump(mode="json")
                                for message in prompt.messages
                            ],
                            "max_tokens": prompt.parameters.max_tokens,
                            "temperature": prompt.parameters.temperature,
                            "stop": prompt.parameters.stop,
                        }
                    else:
                        json_load = {
                            "prompt": prompt.text,
                            "max_tokens": prompt.parameters.max_tokens,
                            "temperature": prompt.parameters.temperature,
                            "stop": prompt.parameters.stop,
                        }
                    response = requests.post(
                        self.api_url,
                        json=json_load,
                        timeout=1000,
                    )
            except Exception as exception:
                raise exception
            if response.status_code != 200:
                warnings.warn(
                    f"Request failed with status code: {response.status_code}"
                )
                return ""
            else:
                result = str(response.json()["text"][0])[len(prompt.text) :]
                if prompt.parameters.stop is not None:
                    if any([stop in result for stop in prompt.parameters.stop]):
                        result = result[
                            : result.index(prompt.parameters.stop[0])
                        ].strip()
                self.cache.set(cache_key, result)
                return result.strip()

    def custom_multi_requests(
        self,
        prompts: List[CustomPrompt],
        progress_desc: Optional[str] = None,
        batch_size: int = 16,
    ) -> List[str]:
        # Create a thread pool to parallelize requests
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Send requests in batches
            responses = list(
                tqdm(
                    executor.map(self.generate, prompts),
                    total=len(prompts),
                    desc=progress_desc,
                )
            )
        return responses

class APIConnectorWithOpenAIFormat(AbstractConnector):
    def __init__(self, api_url: str, cache_path: Optional[str] = None) -> None:
        self.api_url = api_url
        if cache_path is not None:
            self.cache = Cache(cache_path)
        else:
            self.cache = None

    def generate(
        self,
        prompt: CustomPrompt,
    ) -> str:

        cache_key = get_cache_key(prompt)
        if self.cache is not None:
            cached_text = self.cache.get(cache_key)
        else:
            cached_text = None
        if isinstance(cached_text, str):
            return cached_text
        else:
            try:
                if prompt.text is not None:
                    messages_ = [
                        {"role": "user", "content": prompt.text}
                    ]
                elif prompt.messages is not None:
                    messages_ = [
                        message.model_dump(mode="json") for message in prompt.messages
                    ]
                else:
                    raise ValueError("Prompt must contain text or messages")
                response = requests.post(
                    self.api_url,
                    json={
                        "model": prompt.parameters.model_name,
                        "messages": messages_,
                        "temperature": prompt.parameters.temperature,
                        "max_tokens": prompt.parameters.max_tokens,
                        "stop": prompt.parameters.stop,
                    },
                    timeout=1000,
                )
            except Exception as exception:
                raise exception
            if response.status_code != 200:
                warnings.warn(
                    f"Request failed with status code: {response.status_code}"
                )
                return ""
            else:
                try:
                    result = str(response.json()["choices"][0]["message"]["content"])
                    if prompt.parameters.stop is not None:
                        if any([stop in result for stop in prompt.parameters.stop]):
                            result = result[
                                : result.index(prompt.parameters.stop[0])
                            ].strip()
                    if self.cache is not None:
                        self.cache.set(cache_key, result)
                    return result.strip()
                except Exception as exception:
                    raise exception
                    # warnings.warn(
                    #     f"Request failed with this exception: {exception}"
                    # )
                    # return ""

    def custom_multi_requests(
        self,
        prompts: List[CustomPrompt],
        progress_desc: Optional[str] = None,
        batch_size: int = 16,
    ) -> List[str]:
        # Create a thread pool to parallelize requests
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Send requests in batches
            responses = list(
                tqdm(
                    executor.map(self.generate, prompts),
                    total=len(prompts),
                    desc=progress_desc,
                )
            )
        return responses
