import hashlib
import warnings
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Literal, Optional, Union

import backoff
import openai
import requests
from diskcache import Cache
from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm

from aristote.custom_exceptions import NotResponsiveModelError


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class CustomPromptParameters(BaseModel):
    model_name: str
    max_tokens: int = 256
    temperature: float = 0.5
    top_p: Optional[float] = None
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    response_format: Literal["text", "json_object"] = "text"


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


class CustomOpenAIConnector(AbstractConnector):
    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        backoff_max_time: int = 30,
        request_timeout: Optional[int] = None,
        cache_path: Optional[str] = None,
        max_requests_per_second: float = 1.0,
    ):
        AbstractConnector.__init__(self, cache_path=cache_path)
        self.sync_client = OpenAI(api_key=api_key, organization=organization)
        self.backoff_max_time = backoff_max_time
        self.request_timeout = request_timeout
        self.max_requests_per_second = max_requests_per_second
        self.cache = Cache(cache_path)

    # def generate(self, prompt: CustomPrompt) -> str:
    #     text_generation = self.make_request(
    #         prompt=Prompt(
    #             text=prompt.text,
    #             messages=prompt.messages,
    #             parameters=PromptParameters(
    #                 model=prompt.parameters.model_name,
    #                 max_tokens=prompt.parameters.max_tokens,
    #                 temperature=prompt.parameters.temperature,
    #                 stop=prompt.parameters.stop,
    #             ),
    #         )
    #     )
    #     if isinstance(text_generation, TextGeneration):
    #         if isinstance(text_generation.text, str):
    #             return text_generation.text
    #         else:
    #             raise ValueError("Text generation failed")
    #     else:
    #         raise ValueError("Wrong generation type")

    def _generate(
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
                    messages_ = [{"role": "user", "content": prompt.text}]
                elif prompt.messages is not None:
                    messages_ = [
                        message.model_dump(mode="json") for message in prompt.messages
                    ]
                else:
                    raise ValueError("Prompt must contain text or messages")
                response = self.sync_client.chat.completions.create(
                    model=prompt.parameters.model_name,
                    messages=messages_,
                    temperature=prompt.parameters.temperature,
                    max_tokens=prompt.parameters.max_tokens,
                    top_p=prompt.parameters.top_p,
                    seed=prompt.parameters.seed,
                    stop=prompt.parameters.stop,
                    response_format={"type": prompt.parameters.response_format},
                    timeout=self.request_timeout,
                )
            except Exception as exception:
                raise exception
            try:
                result = str(response.choices[0].message.content)
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

    def generate(
        self,
        prompt: CustomPrompt,
    ) -> str:
        """Make asynchronous request using backoff
        that retries the request if it failed.

        Args:
            text (str): prompt text

        Returns:
            str: generated text
        """
        return backoff.on_exception(
            backoff.expo, openai.RateLimitError, max_time=self.backoff_max_time
        )(self._generate)(prompt=prompt)


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


class APIConnectorWithOpenAIFormat(AbstractConnector):
    def __init__(
        self,
        api_url: str,
        token: Optional[str] = None,
        cache_path: Optional[str] = None,
    ) -> None:
        self.api_url = api_url
        self.token = token
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
        cached_text = None
        if isinstance(cached_text, str):
            return cached_text
        else:
            try:
                if prompt.text is not None:
                    messages_ = [{"role": "user", "content": prompt.text}]
                elif prompt.messages is not None:
                    messages_ = [
                        message.model_dump(mode="json") for message in prompt.messages
                    ]
                else:
                    raise ValueError("Prompt must contain text or messages")
                headers = {}
                if self.token:
                    headers["Authorization"] = "Bearer " + self.token

                response = requests.post(
                    self.api_url,
                    json={
                        "model": prompt.parameters.model_name,
                        "messages": messages_,
                        "temperature": prompt.parameters.temperature,
                        "max_tokens": prompt.parameters.max_tokens,
                        "stop": prompt.parameters.stop,
                    },
                    timeout=60000,
                    headers=headers,
                )
            except Exception as exception:
                raise exception
            if response.status_code != 200:
                warnings.warn(
                    f"Request failed with status code: {response.status_code}"
                )
                warnings.warn(f"Request failed content: {response.content}")
                raise NotResponsiveModelError(
                    f"LLM is not responding. Error code : {response.status_code}"
                )
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
