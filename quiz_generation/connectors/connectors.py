import hashlib
import warnings
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import requests
from diskcache import Cache
from illuin_llm_tools import OpenAIConnector, Prompt, PromptParameters, TextGeneration
from pydantic import BaseModel
from tqdm import tqdm


class CustomPromptParametrs(BaseModel):
    model_name: str
    max_tokens: int = 256
    temperature: float = 0.5
    stop: Optional[List[str]] = None


class CustomPrompt(BaseModel):
    text: str
    parameters: CustomPromptParametrs

class AbstractConnector:
    def __init__(self, cache_path: str) -> None:
        self.cache_path = cache_path

    @abstractmethod
    def generate(self, prompt: CustomPrompt) -> str:
        pass

    @abstractmethod
    def custom_multi_requests(self, prompts: List[CustomPrompt]) -> str:
        pass


class CustomOpenAIConnector(OpenAIConnector, AbstractConnector):
    def __init__(self, cache_path: str, max_requests_per_second: float) -> None:
        super().__init__(cache_path)
        self.max_requests_per_second = max_requests_per_second

    def generate(self, prompt: CustomPrompt) -> str:
        text_generation = self.make_request(
            prompt=Prompt(
                text=prompt.text,
                parameters=PromptParameters(
                    model=prompt.parameters.model_name,
                    max_tokens=prompt.parameters.max_tokens,
                    temperature=prompt.parameters.temperature,
                    stop=prompt.parameters.stop,
                )
            )
        )
        if isinstance(text_generation, TextGeneration):
            return text_generation.text
        else:
            raise ValueError("Wring generation type")

    def custom_multi_requests(self, prompts: List[CustomPrompt]) -> List[str]:
        results = self.multi_requests(
            [
                CustomPrompt(
                    text=prompt.text,
                    parameters=CustomPromptParametrs(
                        model_name=prompt.model_name,
                        max_tokens=prompt.max_tokens,
                        temperature=prompt.temperature,
                        stop=prompt.stop,
                    )
                )
                for prompt in prompts
            ],
            max_requests_per_second=self.max_requests_per_second,
        )
        return [result.text for result in results]

def get_cache_key(prompt: CustomPrompt) -> str:
    if prompt.stop is not None:
        stop_str = "-".join(prompt.parameters.stop)
    else:
        stop_str = ""
    str_to_encode = (
        f"{prompt.parameters.model_name}-"
        f"{prompt.parameters.max_tokens}-"
        f"{prompt.parameters.temperature}-"
        f"{stop_str}-"
        f"{prompt.text}"
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
                response = requests.post(
                    self.api_url,
                    json={
                        "prompt": prompt.text,
                        "max_tokens": prompt.parameters.max_tokens,
                        "temperature": prompt.parameters.temperature,
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
                result = str(response.json()["text"][0])[len(prompt.text) :]
                if prompt.parameters.stop is not None:
                    if any([stop in result for stop in prompt.parameters.stop]):
                        result = result[: result.index(prompt.parameters.stop[0])].strip()
                self.cache.set(cache_key, result)
                return result.strip()

    def custom_multi_requests(
        self,
        prompts: List[CustomPrompt],
        batch_size: int = 16,
        description: Optional[str] = None,
    ) -> List[str]:
        # Create a thread pool to parallelize requests
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Send requests in batches
            responses = list(
                tqdm(
                    executor.map(self.generate, prompts),
                    total=len(prompts),
                    desc=description,
                )
            )
        # for response in responses:
        #     if response.status_code == 200:
        #         print("Request was successful")
        #         print(response.json())
        #     else:
        #         print("Request failed with status code:", response.status_code)
        return responses
