from django.db import models

from .core.discord import Channel, get_channels


class DiscordChannelManager(models.Manager):
    def sync(self) -> int:
        """Synchronize list of guild channels objects with the Discord server.

        Return the number of channels.
        """
        from .models import DiscordCategory

        channels = get_channels()
        categories = {
            obj.id: obj for obj in channels if obj.type == Channel.Type.GUILD_CATEGORY
        }
        for category in categories.values():
            DiscordCategory.objects.update_or_create(
                id=category.id, defaults={"name": category.name}
            )
        channel_ids = set()
        text_channels = [obj for obj in channels if obj.type == Channel.Type.GUILD_TEXT]
        for channel in text_channels:
            if channel.parent_id and channel.parent_id in categories:
                category_id = channel.parent_id
            else:
                category_id = None
            self.update_or_create(
                id=channel.id,
                defaults={"name": channel.name, "category_id": category_id},
            )
            channel_ids.add(channel.id)
        self.exclude(id__in=channel_ids).delete()
        DiscordCategory.objects.filter(channels__isnull=True).delete()
        return len(text_channels)
