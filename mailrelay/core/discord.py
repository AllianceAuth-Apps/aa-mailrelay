from typing import Iterable, List, Tuple

import grpc
from discordproxy.discord_api_pb2 import (
    Channel,
    Embed,
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
    return fetch_channels(channel_type=Channel.Type.GUILD_TEXT)


def fetch_channels(channel_type=None) -> Iterable:
    with grpc.insecure_channel("localhost:50051") as channel:
        client = DiscordApiStub(channel)
        request = GetGuildChannelsRequest(guild_id=int(settings.DISCORD_GUILD_ID))
        try:
            response = client.GetGuildChannels(request)
        except grpc.RpcError as ex:
            details = parse_error_details(ex)
            logger.error(
                "gRPC call failed. "
                "HTTP response code: %s\n"
                "JSON error code:%s\n"
                "Discord error message:%s",
                details.status,
                details.code,
                details.text,
            )
            raise DiscordProxyFetchingChannelsFailed()
    channels = response.channels
    if channel_type:
        return [obj for obj in response.channels if obj.type == channel_type]
    return channels


def send_messages_to_channel(
    channel_id: int, messages: List[Tuple[str, Embed]]
) -> None:
    """Send messages to Discord channel"""
    for message in messages:
        with grpc.insecure_channel("localhost:50051") as grpc_channel:
            client = DiscordApiStub(grpc_channel)
            request = SendChannelMessageRequest(
                content=message.content, channel_id=channel_id, embed=message.embed
            )
            try:
                client.SendChannelMessage(request)
            except grpc.RpcError as ex:
                details = parse_error_details(ex)
                logger.error(
                    "gRPC call failed. "
                    "HTTP response code: %s\n"
                    "JSON error code:%s\n"
                    "Discord error message:%s",
                    details.status,
                    details.code,
                    details.text,
                )
                raise DiscordProxySendingMessagesFailed()
