from django.db import models

from .core.discord import fetch_text_channels


class DiscordChannelManager(models.Manager):
    def sync(self) -> int:
        """Synchronize list of guild channels objects with the Discord server.

        Return the number of channels.
        """
        channel_ids = set()
        channels = fetch_text_channels()
        for channel in channels:
            self.update_or_create(id=channel.id, defaults={"name": channel.name})
            channel_ids.add(channel.id)
        self.exclude(id__in=channel_ids).delete()
        return len(channels)
