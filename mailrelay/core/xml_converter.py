from bs4 import BeautifulSoup

from ..utils import is_string_an_url


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
