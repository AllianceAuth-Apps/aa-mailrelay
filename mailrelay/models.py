import datetime as dt
from typing import List

from discordproxy.discord_api_pb2 import Embed
from memberaudit.models import Character, CharacterMail

from django.db import models
from django.utils.timezone import now

from allianceauth.services.hooks import get_extension_logger
from app_utils.datetime import DATETIME_FORMAT
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import MAILRELAY_OLDEST_MAIL_HOURS
from .core.discord import DiscordMessage, send_messages_to_channel
from .core.xml_converter import eve_xml_to_discord_markup
from .managers import DiscordChannelManager
from .utils import chunks_by_lines

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class RelayConfig(models.Model):
    class ChannelPingType(models.TextChoices):
        NONE = "PN", "(none)"
        HERE = "PH", "@here"
        EVERYBODY = "PE", "@everybody"

    class MailCategory(models.TextChoices):
        ALL = "CL", "All mails"
        ALLIANCE = "AM", "Alliance mails"
        CORPORATION = "CM", "Corporation mails"

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    channels = models.ManyToManyField("DiscordChannel")
    is_enabled = models.BooleanField(
        default=True,
        help_text="toogle for activating or deactivating relaying mail",
    )
    mail_category = models.CharField(
        max_length=2,
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
    mails_sent = models.ManyToManyField(
        CharacterMail,
        related_name="+",
        editable=False,
        help_text="Latest mails that have already been sent",
    )

    def __str__(self) -> str:
        return f"#{self.pk}"

    def send_mail(self, mail: CharacterMail, channel: "DiscordChannel"):
        """Send one mail to channel."""
        if not mail.body:
            return
        embeds = self._generate_embeds(mail)
        messages = []
        for num, embed in enumerate(embeds, start=1):
            content = self._content_with_mentions() if num == 1 else ""
            messages.append(DiscordMessage(content=content, embed=embed))
        send_messages_to_channel(channel_id=channel.id, messages=messages)
        self.mails_sent.add(mail)

    def _content_with_mentions(self) -> str:
        if self.ping_type is self.ChannelPingType.EVERYBODY:
            return "@everybody"
        if self.ping_type is self.ChannelPingType.HERE:
            return "@here"
        return ""

    def _generate_embeds(self, mail: CharacterMail) -> List[Embed]:
        recipients = ", ".join(
            [obj.name_plus for obj in mail.recipients.order_by("name")]
        )
        full_description = (
            f"**From**: {mail.sender.name_plus}\n"
            f"**Sent**: {mail.timestamp.strftime(DATETIME_FORMAT)}\n"
            f"**To**: {recipients}\n\n"
        )
        full_description += eve_xml_to_discord_markup(mail.body)
        description_chunks = chunks_by_lines(full_description, 3500)
        chunks_count = len(description_chunks)
        embeds = []
        for num, description_chunk in enumerate(description_chunks, start=1):
            footer_text = f"{num}/{chunks_count}" if chunks_count > 1 else ""
            title = mail.subject if num == 1 else ""
            embeds.append(
                Embed(
                    footer=Embed.Footer(text=footer_text),
                    description=description_chunk,
                    timestamp=mail.timestamp.isoformat(),
                    title=title,
                )
            )
        return embeds

    def new_mails_queryset(self) -> models.QuerySet:
        oldest_timestamp = now() - dt.timedelta(hours=MAILRELAY_OLDEST_MAIL_HOURS)
        self.mails_sent.filter(timestamp__lt=oldest_timestamp).delete()
        new_mails_qs = (
            self.character.mails.select_related("sender")
            .exclude(pk__in=self.mails_sent.values_list("pk", flat=True))
            .filter(timestamp__gte=oldest_timestamp)
        )
        if self.mail_category == self.MailCategory.ALL:
            pass
        elif self.mail_category == self.MailCategory.ALLIANCE:
            alliance_id = self.character.character_ownership.character.alliance_id
            if alliance_id:
                new_mails_qs = new_mails_qs.filter(recipients__id=alliance_id)
            else:
                new_mails_qs = new_mails_qs.none()
        elif self.mail_category == self.MailCategory.CORPORATION:
            corporation_id = self.character.character_ownership.character.corporation_id
            new_mails_qs = new_mails_qs.filter(recipients__id=corporation_id)
        else:
            raise NotImplementedError("Unknown mail category")
        return new_mails_qs


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    last_update_at = models.DateTimeField(auto_now=True)

    objects = DiscordChannelManager()

    def __str__(self) -> str:
        return str(self.name)
