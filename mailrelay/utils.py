from typing import List

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def chunks_by_lines(full_text: str, max_lengths: int) -> List[str]:
    """Converts text into chunks not exceeding max_lengths and splity by newline."""
    parts = list()
    partial_text = ""
    for line in full_text.splitlines(keepends=True):
        if len(partial_text + line) > max_lengths:
            parts.append(partial_text)
            partial_text = ""
        partial_text += line
    if partial_text:
        parts.append(partial_text)
    return parts


def is_string_an_url(url_string: str) -> bool:
    validate_url = URLValidator()
    try:
        validate_url(url_string)
    except ValidationError:
        return False
    return True
