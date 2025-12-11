import json
from typing import Any, Dict, List
from utils.logger import logger


def safe_parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    Safely parse JSON coming from the LLM.
    If there is extra text, try to extract the JSON part.
    """
    raw_text = raw_text.strip()

    # Try direct parse first
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Direct JSON parse failed; trying to extract JSON substring")

    # Try to find first '{' and last '}' and parse substring
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw_text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted JSON substring: {e}")

    # Fallback: empty structure
    return {"entities": [], "relationships": []}


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
