from typing import List

import grpc
from bs4 import BeautifulSoup
from discordproxy.discord_api_pb2 import Embed, SendChannelMessageRequest
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from discordproxy.helpers import parse_error_details

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .utils import is_string_an_url

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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


def send_message_to_discord(channel_id: int, messages: List[str, Embed]) -> bool:
    for message in messages:
        with grpc.insecure_channel("localhost:50051") as grpc_channel:
            client = DiscordApiStub(grpc_channel)
            request = SendChannelMessageRequest(
                content=message.content, channel_id=channel_id, embed=message.embed
            )
            try:
                client.SendChannelMessage(request)
            except grpc.RpcError as e:
                details = parse_error_details(e)
                logger.warning(
                    "gRPC call failed. "
                    "HTTP response code: %s\n"
                    "JSON error code:%s\n"
                    "Discord error message:%s",
                    details.status,
                    details.code,
                    details.text,
                )
                return False
    return True
