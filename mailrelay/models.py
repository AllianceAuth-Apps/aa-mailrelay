import grpc
from discordproxy.discord_api_pb2 import SendChannelMessageRequest
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from memberaudit.models import Character, CharacterMail
from multiselectfield import MultiSelectField

from django.db import models


class RelayConfig(models.Model):
    class ChannelPingType(models.TextChoices):
        NONE = "PN", "(none)"
        HERE = "PH", "@here"
        EVERYBODY = "PE", "@everybody"

    class MailCategory(models.TextChoices):
        ALLIANCE = "AL", "alliance"
        CORPORATION = "CP", "corporation"

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    channels = models.ManyToManyField("DiscordChannel")
    is_enabled = models.BooleanField(
        default=True,
        help_text="toogle for activating or deactivating relaying mail",
    )
    notification_types = MultiSelectField(
        choices=MailCategory.choices,
        help_text="Category of mails that you want to relay to Discord.",
    )
    ping_type = models.CharField(
        max_length=2,
        choices=ChannelPingType.choices,
        default=ChannelPingType.NONE,
        verbose_name="channel pings",
        help_text="Option to ping every member of the channel",
    )
    mails_sent = models.ManyToManyField(CharacterMail, related_name="+")

    def __str__(self) -> str:
        return str(self.pk)

    def send_new_mails(self):
        new_mails = self.character.mails.exclude(
            pk__in=self.mails_sent.values_list("pk", flat=True)
        ).order_by("-timestamp")[5:]
        with grpc.insecure_channel("localhost:50051") as channel:
            client = DiscordApiStub(channel)
            for mail in new_mails:
                for channel in self.channels.all():
                    request = SendChannelMessageRequest(
                        channel_id=channel.id, content=mail.body[:1999]
                    )
                    client.SendChannelMessage(request)


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    last_update_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)
