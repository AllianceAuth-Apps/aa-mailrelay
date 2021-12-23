from typing import Iterable

import grpc
from discordproxy.discord_api_pb2 import Channel, GetGuildChannelsRequest
from discordproxy.discord_api_pb2_grpc import DiscordApiStub

from django.conf import settings
from django.db import models


class DiscordChannelManager(models.Manager):
    def sync(self):
        """Synchronize list of guild channels objects with the Discord server."""
        channel_ids = set()
        for channel in self._fetch_discord_channels():
            if channel.type == Channel.Type.GUILD_TEXT:
                self.update_or_create(id=channel.id, defaults={"name": channel.name})
                channel_ids.add(channel.id)
        self.exclude(id__in=channel_ids).delete()

    def _fetch_discord_channels(self) -> Iterable:
        with grpc.insecure_channel("localhost:50051") as channel:
            client = DiscordApiStub(channel)
            request = GetGuildChannelsRequest(guild_id=int(settings.DISCORD_GUILD_ID))
            response = client.GetGuildChannels(request)
        return response.channels
