import grpc
from discordproxy.discord_api_pb2 import Embed, SendChannelMessageRequest
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from memberaudit.models import Character, CharacterMail
from multiselectfield import MultiSelectField

from django.db import models

from allianceauth.services.hooks import get_extension_logger
from app_utils.datetime import DATETIME_FORMAT
from app_utils.logging import LoggerAddTag

from . import __title__
from .core import chunks_by_lines, eve_xml_to_discord_markup

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
        return f"#{self.pk}"

    def send_new_mails(self):
        new_mails = self.character.mails.exclude(
            pk__in=self.mails_sent.values_list("pk", flat=True)
        ).order_by("timestamp")[:3]
        if not new_mails.exists():
            logger.info("No new mails to forward.")
            return
        with grpc.insecure_channel("localhost:50051") as channel:
            logger.info(
                "Forwarding %s eve mails to %s channel(s).",
                new_mails.count(),
                self.channels.count(),
            )
            client = DiscordApiStub(channel)
            for mail in new_mails:
                recipients = ", ".join(
                    [obj.name_plus for obj in mail.recipients.order_by("name")]
                )
                full_description = (
                    f"**From**: {mail.sender.name_plus}\n"
                    f"**To**: {recipients}\n"
                    f"**Sent**: {mail.timestamp.strftime(DATETIME_FORMAT)}\n\n"
                )
                full_description += eve_xml_to_discord_markup(mail.body)
                for channel in self.channels.all():
                    description_chunks = chunks_by_lines(full_description, 3500)
                    chunks_count = len(description_chunks)
                    for num, description_chunk in enumerate(
                        description_chunks, start=1
                    ):
                        footer_text = (
                            f"{num}/{chunks_count}" if chunks_count > 1 else ""
                        )
                        title = mail.subject if num == 1 else ""
                        embed = Embed(
                            footer=Embed.Footer(text=footer_text),
                            description=description_chunk,
                            timestamp=mail.timestamp.isoformat(),
                            title=title,
                        )
                        request = SendChannelMessageRequest(
                            channel_id=channel.id, embed=embed
                        )
                        client.SendChannelMessage(request)
                self.mails_sent.add(mail)


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    last_update_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)
