from __future__ import annotations

import json
import re
from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)


def extract_json_from_text(text: str) -> str | None:
    """
    Extracts a JSON string from text that might contain other content.
    Handles markdown code blocks, extra whitespace, and other formatting.
    Returns None if no valid JSON is found.
    """
    if not text:
        return None

    # First try to find JSON in markdown code blocks
    match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\s*({.*?})\s*```", text, re.DOTALL)

    if match:
        json_candidate = match.group(1)
        # Use the helper function to find complete JSON
        json_str = _find_complete_json(json_candidate)
        if json_str:
            try:
                json.loads(json_str)
                return json_str
            except Exception:
                pass

    # If no markdown block found or invalid, search for JSON in the entire text
    # Find the first opening brace
    start_pos = text.find("{")
    if start_pos == -1:
        return None

    # Use the helper function to find complete JSON starting from the first brace
    json_str = _find_complete_json(text[start_pos:])
    if json_str:
        try:
            json.loads(json_str)
            return json_str
        except Exception:
            pass

    return None


def _find_complete_json(text: str) -> str | None:
    """
    Znajduje kompletny JSON w tekście, obsługując zagnieżdżone struktury.
    """
    if not text or not text.strip().startswith("{"):
        return None

    brace_count = 0
    in_string = False
    escape_next = False
    start_pos = text.find("{")

    for i, char in enumerate(text[start_pos:], start_pos):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    # Znaleziono kompletny JSON
                    return text[start_pos : i + 1]

    return None
