import os
import base64
import re
import signal

from openai import OpenAI


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "example"))


class GPT4:
    def __init__(self, model="gpt-4-1106-preview", temperature=0.2, max_tokens=300):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.messages = []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_response(self):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        print(f"Full response: {completion}")
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


def remove_error_source(message: str) -> str:
    """
    Strip the leading error source from a Lean error message.

    Example:
    >>> remove_error_source(
        "/home/johndoe/.../LeanEuclid/result/proof/Book/text-only/0shot/2.lean:6:35: error: ..."
    )
    error: ...
    """
    return re.sub(r"/[^:]+:\d+:\d+: ", "", message)


def kill_process_group(pgid: int) -> None:
    """
    Kill all processes in the process group using ``SIGKILL``.
    Useful for killing z3 and cvc5 solvers spawned by a checker.

    :param pgid: ID of the process group to kill
    """
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        # Process group already exited
        pass
    except PermissionError:
        print("⚠️  Insufficient permission to kill process group", pgid)
