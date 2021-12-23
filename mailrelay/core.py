from typing import List

from bs4 import BeautifulSoup

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def eve_xml_to_discord_markup(xml_doc: str) -> str:
    """Converts Eve Online xml to Discord markup."""
    soup = BeautifulSoup(xml_doc, "html.parser")
    for element in soup.find_all("loc"):
        element.unwrap()
    for element in soup.find_all("br"):
        element.replace_with("\n")
    for element in soup.find_all("b"):
        element.replace_with(f"**{element.string}**")
    for element in soup.find_all("i"):
        element.replace_with(f"_{element.string}_")
    for element in soup.find_all("u"):
        element.replace_with(f"__{element.string}__")
    for element in soup.find_all("a"):
        link = element["href"]
        text = element.string
        if is_string_an_url(link):
            element.replace_with(f"[{link}]({text})")
        else:
            element.replace_with(f"**{text}**")
    return soup.get_text()


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
