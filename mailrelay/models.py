import datetime as dt

import grpc
from discordproxy.discord_api_pb2 import Embed, SendChannelMessageRequest
from discordproxy.discord_api_pb2_grpc import DiscordApiStub
from discordproxy.helpers import parse_error_details
from memberaudit.models import Character, CharacterMail

from django.db import models
from django.utils.timezone import now

from allianceauth.services.hooks import get_extension_logger
from app_utils.datetime import DATETIME_FORMAT
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import MAILRELAY_OLDEST_MAIL_HOURS
from .core import chunks_by_lines, eve_xml_to_discord_markup
from .managers import DiscordChannelManager

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class RelayConfig(models.Model):
    class ChannelPingType(models.TextChoices):
        NONE = "PN", "(none)"
        HERE = "PH", "@here"
        EVERYBODY = "PE", "@everybody"

    class MailCategory(models.TextChoices):
        ALLIANCE = "AL", "Alliance mails"
        CORPORATION = "CP", "Corporation mails"

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

    def send_new_mails(self):
        """Send all new mails to configured channels."""
        new_mails = self.new_mails_queryset()
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
            for mail in new_mails.order_by("timestamp"):
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
                    self._send_message_to_discord(
                        client=client,
                        mail=mail,
                        channel=channel,
                        full_description=full_description,
                    )
                self.mails_sent.add(mail)

    def new_mails_queryset(self) -> models.QuerySet:
        oldest_timestamp = now() - dt.timedelta(hours=MAILRELAY_OLDEST_MAIL_HOURS)
        self.mails_sent.filter(timestamp__lt=oldest_timestamp).delete()
        new_mails_qs = (
            self.character.mails.select_related("sender")
            .exclude(pk__in=self.mails_sent.values_list("pk", flat=True))
            .filter(timestamp__gte=oldest_timestamp)
        )
        if self.mail_category == self.MailCategory.ALLIANCE:
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

    def _send_message_to_discord(self, client, mail, channel, full_description):
        description_chunks = chunks_by_lines(full_description, 3500)
        chunks_count = len(description_chunks)
        for num, description_chunk in enumerate(description_chunks, start=1):
            footer_text = f"{num}/{chunks_count}" if chunks_count > 1 else ""
            title = mail.subject if num == 1 else ""
            embed = Embed(
                footer=Embed.Footer(text=footer_text),
                description=description_chunk,
                timestamp=mail.timestamp.isoformat(),
                title=title,
            )
            content = self._content_with_mentions()
            request = SendChannelMessageRequest(
                content=content, channel_id=channel.id, embed=embed
            )
            try:
                client.SendChannelMessage(request)
            except grpc.RpcError as e:
                details = parse_error_details(e)
                logger.warning(
                    "gRPC call failed. "
                    "HTTP response code: %s\n"
                    "JSON error code:%s\n"
                    "Discord error message:%s",
                    details.status,
                    details.code,
                    details.text,
                )

    def _content_with_mentions(self) -> str:
        if self.ping_type is self.ChannelPingType.EVERYBODY:
            return "@everybody"
        if self.ping_type is self.ChannelPingType.HERE:
            return "@here"
        return ""


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    last_update_at = models.DateTimeField(auto_now=True)

    objects = DiscordChannelManager()

    def __str__(self) -> str:
        return str(self.name)
