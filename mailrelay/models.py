import datetime as dt
from typing import List, Optional

from discordproxy.client import DiscordClient
from discordproxy.discord_api_pb2 import Embed
from memberaudit.models import Character, CharacterMail

from django.db import models
from django.utils.timezone import now

from allianceauth.services.hooks import get_extension_logger
from app_utils.datetime import DATETIME_FORMAT
from app_utils.logging import LoggerAddTag
from app_utils.urls import static_file_absolute_url

from . import __title__
from .app_settings import MAILRELAY_OLDEST_MAIL_HOURS, MAILRELAY_RELAY_GRACE_MINUTES
from .core.xml_converter import eve_xml_to_discord_markup
from .managers import DiscordChannelManager
from .utils import chunks_by_lines

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class RelayConfig(models.Model):
    class ChannelPingType(models.TextChoices):
        NONE = "PN", "(none)"
        HERE = "PH", "@here"
        EVERYBODY = "PE", "@everybody"  # TODO: Rename to EVERYONE with next migration

    class MailCategory(models.TextChoices):
        ALL = "AL", "All mails"
        ALLIANCE = "AM", "Alliance mails"
        CORPORATION = "CM", "Corporation mails"

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    discord_channel = models.ForeignKey(
        "DiscordChannel", on_delete=models.SET_NULL, null=True
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Toogle for activating or deactivating relaying mails.",
    )
    last_service_run_at = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        help_text="Time of last successful service run.",
    )
    mail_category = models.CharField(
        max_length=2,
        choices=MailCategory.choices,
        help_text="Category of mails that you want to relay to Discord.",
    )
    mails_sent = models.ManyToManyField(
        CharacterMail,
        related_name="+",
        editable=False,
        help_text="Latest mails that have already been sent.",
    )
    ping_type = models.CharField(
        max_length=2,
        choices=ChannelPingType.choices,
        default=ChannelPingType.NONE,
        verbose_name="channel pings",
        help_text="Option to ping every member of the channel.",
    )

    def __str__(self) -> str:
        return f"#{self.pk}"

    @property
    def is_service_up(self) -> Optional[bool]:
        if not self.last_service_run_at:
            return None
        return now() - self.last_service_run_at < dt.timedelta(
            minutes=MAILRELAY_RELAY_GRACE_MINUTES
        )

    def new_mails_queryset(self) -> models.QuerySet:
        """Determine which mails have not yet been sent."""
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
            raise NotImplementedError(f"Unknown mail category: {self.mail_category}")
        return new_mails_qs

    def send_mail(self, mail: CharacterMail, timeout: int = None) -> None:
        """Send one mail to channel.

        Args:
        - mail: mail to be sent
        - timeout: timeout for request to Discord in seconds
        """
        if not mail.body:
            return
        if not self.discord_channel:
            raise ValueError(f"No channel configured for config {self}")
        client = DiscordClient(timeout=timeout)
        embeds = self._generate_embeds(mail)
        for num, embed in enumerate(embeds, start=1):
            content = self._content_with_mentions() if num == 1 else ""
            client.create_channel_message(
                channel_id=self.discord_channel.id, content=content, embed=embed
            )
        self.mails_sent.add(mail)

    def _content_with_mentions(self) -> str:
        if self.ping_type == self.ChannelPingType.EVERYBODY:
            mention = "@everyone "
        elif self.ping_type == self.ChannelPingType.HERE:
            mention = "@here "
        else:
            mention = ""
        if self.mail_category == self.MailCategory.ALLIANCE:
            title = "Alliance"
        elif self.mail_category == self.MailCategory.CORPORATION:
            title = "Corporation"
        else:
            title = "Eve"
        return f"{mention}**New {title} Mail**"

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
        footer_icon_url = static_file_absolute_url("mailrelay/mailrelay_logo.png")
        embeds = []
        for num, description_chunk in enumerate(description_chunks, start=1):
            footer_text = __title__
            footer_text += f" {num}/{chunks_count}" if chunks_count > 1 else ""
            title = mail.subject if num == 1 else ""
            embeds.append(
                Embed(
                    footer=Embed.Footer(text=footer_text, icon_url=footer_icon_url),
                    description=description_chunk,
                    timestamp=mail.timestamp.isoformat(),
                    title=title,
                )
            )
        return embeds

    def record_service_run(self):
        """Record successful service run."""
        self.last_service_run_at = now()
        self.save(update_fields=["last_service_run_at"])


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(
        "DiscordCategory",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="channels",
    )
    last_update_at = models.DateTimeField(auto_now=True)

    objects = DiscordChannelManager()

    def __str__(self) -> str:
        if self.category:
            return f"{self.category.name} / {self.name}"
        return str(self.name)


class DiscordCategory(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    last_update_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)
