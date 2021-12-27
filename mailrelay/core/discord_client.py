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
    """General error that occured while interacting with Discord."""


class DiscordClient:
    """Client for interacting with Discord."""

    def __init__(self, target: str = None, options=None) -> None:
        """
        Args:
        - target: The server address. Default is: "localhost:50051"
        - options: An optional list of key-value pairs to configure the channel.
        """
        self.target = str(target) if target else "localhost:50051"
        self.options = options

    def get_text_channels(self) -> Iterable[Channel]:
        """Get all text channels."""
        return [
            obj for obj in self.get_channels() if obj.type == Channel.Type.GUILD_TEXT
        ]

    def get_channels(self) -> Iterable[Channel]:
        """Get all channels."""
        with grpc.insecure_channel(self.target, self.options) as channel:
            client = DiscordApiStub(channel)
            request = GetGuildChannelsRequest(guild_id=int(settings.DISCORD_GUILD_ID))
            try:
                response = client.GetGuildChannels(request)
            except grpc.RpcError as ex:
                error_text = self._log_grpc_error(ex)
                raise DiscordError(error_text)
        return response.channels

    def create_channel_message(
        self, channel_id: int, content: str = "", embed: Embed = None
    ) -> Message:
        """Create new message in a channel."""
        if not content and not embed:
            raise ValueError("Either content or embed need to be specified.")
        with grpc.insecure_channel(self.target, self.options) as grpc_channel:
            client = DiscordApiStub(grpc_channel)
            request = SendChannelMessageRequest(
                content=content, channel_id=channel_id, embed=embed
            )
            try:
                response = client.SendChannelMessage(request)
                return response.message
            except grpc.RpcError as ex:
                error_text = self._log_grpc_error(ex)
                raise DiscordError(error_text)

    @staticmethod
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
