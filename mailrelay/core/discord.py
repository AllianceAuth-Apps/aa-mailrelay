from typing import Iterable

import grpc
from discordproxy.discord_api_pb2 import (
    Channel,
    Embed,
    GetGuildChannelsRequest,
    Message,
    SendChannelMessageRequest,
)
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from discordproxy.helpers import parse_error_details

from django.conf import settings

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from .. import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class DiscordError(Exception):
    pass


def get_text_channels() -> Iterable:
    """Get all text channels."""
    return _get_channels(channel_type=Channel.Type.GUILD_TEXT)


def _get_channels(channel_type=None) -> Iterable:
    with grpc.insecure_channel("localhost:50051") as channel:
        client = DiscordApiStub(channel)
        request = GetGuildChannelsRequest(guild_id=int(settings.DISCORD_GUILD_ID))
        try:
            response = client.GetGuildChannels(request)
        except grpc.RpcError as ex:
            error_text = _log_grpc_error(ex)
            raise DiscordError(error_text)
    channels = response.channels
    if channel_type:
        return [obj for obj in response.channels if obj.type == channel_type]
    return channels


def create_channel_message(
    channel_id: int, content: str = "", embed: Embed = None
) -> Message:
    """Create new message in a channel."""
    if not content and not embed:
        raise ValueError("Either content or embed need to be specified.")
    with grpc.insecure_channel("localhost:50051") as grpc_channel:
        client = DiscordApiStub(grpc_channel)
        request = SendChannelMessageRequest(
            content=content, channel_id=channel_id, embed=embed
        )
        try:
            response = client.SendChannelMessage(request)
            return response.message
        except grpc.RpcError as ex:
            error_text = _log_grpc_error(ex)
            raise DiscordError(error_text)


def _log_grpc_error(ex) -> str:
    details = parse_error_details(ex)
    logger.error(
        "gRPC call failed. HTTP response code: %s, JSON error code:%s, "
        "Discord error message: %s",
        details.status,
        details.code,
        details.text,
    )
    return details.text
