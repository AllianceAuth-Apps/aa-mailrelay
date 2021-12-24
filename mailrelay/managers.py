from django.db import models

from .core.discord import fetch_text_channels


class DiscordChannelManager(models.Manager):
    def sync(self):
        """Synchronize list of guild channels objects with the Discord server."""
        channel_ids = set()
        for channel in fetch_text_channels():
            self.update_or_create(id=channel.id, defaults={"name": channel.name})
            channel_ids.add(channel.id)
        self.exclude(id__in=channel_ids).delete()
