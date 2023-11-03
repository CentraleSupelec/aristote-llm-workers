import hashlib
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import requests
from diskcache import Cache
from pydantic import BaseModel
from tqdm import tqdm


class Prompt(BaseModel):
    text: str
    model_name: str
    max_tokens: int = 256
    temperature: float = 0.5
    stop: Optional[List[str]] = None


def get_cache_key(prompt: Prompt) -> str:
    if prompt.stop is not None:
        stop_str = "-".join(prompt.stop)
    else:
        stop_str = ""
    str_to_encode = (
        f"{prompt.model_name}-"
        f"{prompt.max_tokens}-"
        f"{prompt.temperature}-"
        f"{stop_str}-"
        f"{prompt.text}"
    )
    return str(hashlib.sha256(str_to_encode.encode()).hexdigest())


class APIConnector:
    def __init__(self, api_url: str, cache_path: str) -> None:
        self.api_url = api_url
        self.cache = Cache(cache_path)

    def generate(
        self,
        prompt: Prompt,
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
                        "max_tokens": prompt.max_tokens,
                        "temperature": prompt.temperature,
                        "stop": prompt.stop,
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
                if prompt.stop is not None:
                    if any([stop in result for stop in prompt.stop]):
                        result = result[: result.index(prompt.stop[0])].strip()
                self.cache.set(cache_key, result)
                return result.strip()

    def multi_requests(
        self,
        prompts: List[Prompt],
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
