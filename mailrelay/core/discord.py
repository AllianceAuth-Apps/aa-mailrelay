from collections import namedtuple
from typing import Iterable, List

import grpc
from discordproxy.discord_api_pb2 import (
    Channel,
    GetGuildChannelsRequest,
    SendChannelMessageRequest,
)
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from discordproxy.helpers import parse_error_details

from django.conf import settings

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from .. import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class DiscordProxyError(Exception):
    pass


class DiscordProxyFetchingChannelsFailed(DiscordProxyError):
    pass


class DiscordProxySendingMessagesFailed(DiscordProxyError):
    pass


def fetch_text_channels() -> Iterable:
    return _fetch_channels(channel_type=Channel.Type.GUILD_TEXT)


def _fetch_channels(channel_type=None) -> Iterable:
    with grpc.insecure_channel("localhost:50051") as channel:
        client = DiscordApiStub(channel)
        request = GetGuildChannelsRequest(guild_id=int(settings.DISCORD_GUILD_ID))
        try:
            response = client.GetGuildChannels(request)
        except grpc.RpcError as ex:
            error_text = _log_grpc_error(ex)
            raise DiscordProxyFetchingChannelsFailed(error_text)
    channels = response.channels
    if channel_type:
        return [obj for obj in response.channels if obj.type == channel_type]
    return channels


DiscordMessage = namedtuple("DiscordMessage", ["channel_id", "content", "embed"])


def send_messages_to_channels(messages: List[DiscordMessage]) -> None:
    """Send messages to Discord channel"""
    for message in messages:
        with grpc.insecure_channel("localhost:50051") as grpc_channel:
            client = DiscordApiStub(grpc_channel)
            request = SendChannelMessageRequest(
                content=message.content,
                channel_id=message.channel_id,
                embed=message.embed,
            )
            try:
                client.SendChannelMessage(request)
            except grpc.RpcError as ex:
                error_text = _log_grpc_error(ex)
                raise DiscordProxySendingMessagesFailed(error_text)


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
