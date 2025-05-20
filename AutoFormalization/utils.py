import os
import base64
from abc import ABCMeta, abstractmethod
from typing import Any, Final, override

from openai import OpenAI, AzureOpenAI
from openai.types.chat import ChatCompletionMessageParam

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "example"))


class LanguageModel(metaclass=ABCMeta):
    _model: Final[str]
    temperature: float
    max_tokens: int

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 300):
        self._model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def add_message(self, role: str, content: str) -> Any:
        pass

    @abstractmethod
    def get_response(self) -> str:
        pass


class AzureModel(LanguageModel):
    _messages: list[ChatCompletionMessageParam]
    _client: Any

    @override
    def __init__(self, model: str):
        super().__init__(model)

        # resolve type mismatch error
        assert (endpoint := os.getenv("AZURE_OPENAI_ENDPOINT")) is not None

        self._client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=endpoint,
            api_version="2024-10-21",
        )
        self._messages = []

    @override
    def add_message(self, role, content) -> None:
        self._messages.append({"role": role, "content": content})

    @override
    def get_response(self) -> str:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=self._messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content


class GPT4(LanguageModel):
    _messages: list[dict[str, str]]
    _client: Any

    @override
    def __init__(
        self,
        model: str = "gpt-4-1106-preview",
        temperature: float = 0.2,
        max_tokens: int = 300,
    ):
        super().__init__(model, temperature, max_tokens)
        self._client = OpenAI()
        self._messages = []

    @override
    def add_message(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    @override
    def get_response(self) -> str:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=self._messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content


def process_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


def lean_error(error):
    return f"Your formalized statement is not a well-formed lean expression.\nHere is the error messsage from Lean: {error}\nPlease output a fixed version of the formalization."


def parse_error():
    return "Your output is not in the desired format. Please output the formalized statement within triple angle brackets (<<< Lean expression here >>>)."


def format_content(dataset, namespace, theorem_name, theorem, proof):
    if dataset == "UniGeo":
        result = f"""import SystemE
import Book
import UniGeo.Relations

open Elements.Book1

namespace {namespace}

theorem {theorem_name} : {theorem} := by

{proof}

end {namespace}
"""
    elif dataset == "Book":
        result = f"""import SystemE
import Book

namespace {namespace}

theorem {theorem_name} : {theorem} := by

{proof}

end {namespace}
"""
    return result
