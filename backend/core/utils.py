import json
import re


def extract_json_from_text(text: str) -> str | None:
    """
    Extracts a JSON string from text that might contain other content.
    Returns None if no valid JSON is found.
    """
    # Look for JSON-like content between curly braces
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)
    try:
        # Validate that it's actually JSON
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        return None
