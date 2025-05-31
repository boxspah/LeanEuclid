"""
analyze_equiv.py

Counts occurrences of the *binary_check* field across a directory of equivalence checker
results.

Only the values ``"no_conclusion"``, ``"ground_imp_test"``, ``"test_imp_ground"``, and
``"equiv"`` are permitted. Any other value triggers :class:`ValueError`.

Usage
-----
.. code-block:: console

    $ python analyze_equiv.py /path/to/json_dir

The script prints a report like::

    equiv             8
    ground_imp_test   1
    test_imp_ground   9
    no_conclusion    20

Exit status is non‑zero on error.
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter
from typing import Final

ALLOWED_VALUES: Final[list[str]] = [
    "equiv",
    "ground_imp_test",
    "test_imp_ground",
    "no_conclusion",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count occurrences of the 'binary_check' field in JSON files."
    )
    parser.add_argument(
        "directory", type=Path, help="Path to the directory containing JSON files"
    )
    return parser.parse_args()


def extract_binary_check(file_path: Path) -> str:
    """
    Return the *binary_check* value from ``file_path`` or raise on invalid schema.
    """
    try:
        data = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"File {file_path} is not valid JSON") from e

    if not isinstance(data, dict) or len(data) != 1:
        raise ValueError(f"Unexpected top‑level structure in {file_path}")

    inner_object = next(iter(data.values()))
    if not isinstance(inner_object, dict) or "binary_check" not in inner_object:
        raise ValueError(f"'binary_check' missing in {file_path}")

    value = inner_object["binary_check"]
    if value not in ALLOWED_VALUES:
        raise ValueError(f"Unknown binary_check value '{value}' in {file_path}")

    return value


def count_binary_checks(directory: Path) -> Counter[str]:
    """
    Traverse ``directory`` non-recursively and accumulate *binary_check* value frequencies.
    """
    if not directory.is_dir():
        raise ValueError(f"{directory} is not a directory")

    counter: Counter[str] = Counter()
    for file_path in sorted(directory.iterdir()):
        if file_path.is_file() and file_path.suffix == ".json":
            value = extract_binary_check(file_path)
            counter[value] += 1

    return counter


def main() -> None:
    args = parse_args()
    try:
        counts = count_binary_checks(args.directory)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for value in ALLOWED_VALUES:
        print(f"{value:<16} {counts.get(value, 0)}")


if __name__ == "__main__":
    main()
