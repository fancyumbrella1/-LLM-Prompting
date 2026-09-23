"""Read the lost-and-found database and save structured results."""

import json
from pathlib import Path


def load_items(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["items"]


def get_unclaimed_items(items):
    return [item for item in items if item["status"].casefold() == "unclaimed"]


def save_result(result, filename):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
