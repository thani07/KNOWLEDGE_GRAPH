import re


def clean_text(text: str) -> str:
    """Basic cleanup of whitespace and weird characters."""
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Trim
    text = text.strip()
    return text
