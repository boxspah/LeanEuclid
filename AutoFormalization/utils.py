import os
import base64
from abc import ABCMeta, abstractmethod
from typing import Any, Final, override, cast

from openai import OpenAI, AzureOpenAI
from openai.types.chat import ChatCompletionMessageParam

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "example"))


class LanguageModel(metaclass=ABCMeta):
    def __init__(self, model: str, **request_params):
        self._model: Final[str] = model
        self._request_params = request_params

    @abstractmethod
    def add_message(self, role: str, content: str) -> Any:
        pass

    @abstractmethod
    def get_response(self) -> str:
        pass


class AzureModel(LanguageModel):
    @override
    def __init__(self, model: str, **request_params):
        super().__init__(model, **request_params)
        self._client = AzureOpenAI(api_version="2024-12-01-preview")
        self._messages: list[ChatCompletionMessageParam] = []

    @override
    def add_message(self, role: str, content: str) -> None:
        self._messages.append(
            cast(ChatCompletionMessageParam, {"role": role, "content": content})
        )

    @override
    def get_response(self) -> str:
        completion = self._client.chat.completions.create(
            model=self._model, messages=self._messages, **self._request_params
        )
        return completion.choices[0].message.content


class GPT4(LanguageModel):
    @override
    def __init__(
        self,
        model: str = "gpt-4-1106-preview",
        temperature: float = 0.2,
        max_tokens: int = 300,
    ):
        super().__init__(model, temperature=temperature, max_tokens=max_tokens)
        self._client = OpenAI()
        self._messages: list[ChatCompletionMessageParam] = []

    @override
    def add_message(self, role: str, content: str) -> None:
        self._messages.append(
            cast(ChatCompletionMessageParam, {"role": role, "content": content})
        )

    @override
    def get_response(self) -> str:
        completion = self._client.chat.completions.create(
            model=self._model, messages=self._messages, **self._request_params
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
