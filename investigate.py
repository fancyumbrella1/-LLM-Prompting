"""Find possible lost-item matches with Qwen and validate its JSON output."""

import json
import os
from pathlib import Path

from parse_data import get_unclaimed_items, load_items, save_result


def build_prompt(description, available_items):
    system_prompt = (
        "You are a campus lost-and-found matching assistant. Use ONLY the "
        "provided JSON items as evidence. Include every plausible match; not "
        "all item details need to match, but the item type must be compatible. "
        "A shared color or location alone is not enough. Do not invent IDs. Return ONLY one "
        'valid JSON object with exactly two keys: {"matches": ["ITEM_ID"], '
        '"confidence": "LOW"}. matches must be a list of matching IDs, or [] '
        "if none match. confidence must be exactly LOW, MEDIUM, or HIGH. "
        "Do not add markdown or explanations."
    )
    user_prompt = (
        f"Lost item description:\n{description.strip()}\n\n"
        "Available unclaimed items (the only source you may use):\n"
        f"{json.dumps(available_items, ensure_ascii=False)}"
    )
    return system_prompt, user_prompt


def ask_qwen(system_prompt, user_prompt):
    from ollama import chat

    return chat(
        model=os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
    )


def parse_response(response_text):
    return json.loads(response_text)


def validate_result(result, available_items):
    if not isinstance(result, dict) or set(result) != {"matches", "confidence"}:
        raise ValueError("Qwen must return exactly matches and confidence.")
    matches = result["matches"]
    if not isinstance(matches, list) or not all(isinstance(item, str) for item in matches):
        raise ValueError("matches must be a list of item IDs.")
    if result["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("confidence must be LOW, MEDIUM, or HIGH.")
    valid_ids = {item["id"] for item in available_items}
    if any(item_id not in valid_ids for item_id in matches):
        raise ValueError("Qwen returned an ID that is not available.")
    if len(matches) != len(set(matches)):
        raise ValueError("Qwen returned a duplicate ID.")
    return result


def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f'Confidence: {result["confidence"]}')
    if not result["matches"]:
        print("No possible matches found.")
        print("Matches: []")
        return
    by_id = {item["id"]: item for item in available_items}
    print("\nPossible matches:")
    for item_id in result["matches"]:
        item = by_id[item_id]
        print(f'\nID: {item_id}')
        print(f'Item: {item["item"]}')
        print(f'Color: {item["color"]}')
        print(f'Location: {item["location"]}')
        print(f'Date found: {item["date"]}')


def main():
    root = Path(__file__).parent
    available_items = get_unclaimed_items(load_items(root / "found_items.json"))
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    description = input("Describe the item you lost: ").strip()
    if not description:
        print("Please provide a description.")
        return
    print("\nSearching for possible matches...")
    system_prompt, user_prompt = build_prompt(description, available_items)
    response = ask_qwen(system_prompt, user_prompt)
    result = validate_result(parse_response(response.message.content), available_items)
    display_matches(result, available_items)
    output = root / "output" / "match_result.json"
    save_result(result, output)
    print(f"\nResult saved to {output}")


if __name__ == "__main__":
    main()
