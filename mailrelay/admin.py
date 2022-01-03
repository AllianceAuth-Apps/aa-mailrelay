from collections import defaultdict

from discordproxy.client import DiscordClient
from discordproxy.exceptions import DiscordProxyException

from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import MAILRELAY_DISCORD_USER_TIMEOUT
from .models import DiscordCategory, DiscordChannel, RelayConfig

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class RelayConfigForm(ModelForm):
    class Meta:
        model = RelayConfig
        fields = (
            "character",
            "mail_category",
            "discord_channel",
            "ping_type",
            "is_enabled",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        channel_choices = self._generate_choices_for_discord_channel()
        self.fields["discord_channel"].choices = channel_choices.items()

    @staticmethod
    def _generate_choices_for_discord_channel() -> dict:
        channel_choices = defaultdict(list)
        channel_choices[None] = [(None, "---------")]
        for obj in DiscordChannel.objects.select_related("category").order_by(
            "category__name", "name"
        ):
            category_name = obj.category.name if obj.category else None
            channel_choices[category_name].append((obj.pk, obj.name))
        return channel_choices


@admin.register(RelayConfig)
class RelayConfigAdmin(admin.ModelAdmin):
    change_list_template = "admin/mailrelay/relayconfig/change_list.html"
    form = RelayConfigForm
    list_display = (
        "__str__",
        "character",
        "_organization",
        "mail_category",
        "_channel",
        "is_enabled",
        "last_service_run_at",
        "_is_service_up",
    )
    ordering = ("pk",)

    actions = ["send_test_message"]

    if settings.DEBUG:
        actions += ["resent_mails"]

    autocomplete_fields = ["character"]

    @admin.display(ordering="discord_channel")
    def _channel(self, obj) -> str:
        if not obj.discord_channel:
            return format_html(
                '<span style="color:red;"><b>Error: No channel configured</b></span>'
            )
        return str(obj.discord_channel)

    @admin.display(boolean=True)
    def _is_service_up(self, obj) -> bool:
        return obj.is_service_up

    def _organization(self, obj) -> str:
        eve_character = obj.character.character_ownership.character
        return format_html(
            "{}<br>{}",
            eve_character.corporation_name,
            eve_character.alliance_name if eve_character.alliance_name else "",
        )

    @admin.action(description="Send test message for selected configurations")
    def send_test_message(self, request, queryset):
        items_count = 0
        client = DiscordClient()
        for obj in queryset:
            try:
                client.create_channel_message(
                    channel_id=obj.discord_channel.id,
                    content=f"Test message from {__title__}",
                )
            except DiscordProxyException as ex:
                logger.error("%s: Failed to send test message for", obj, exc_info=True)
                self.message_user(
                    request,
                    f"{obj}: Failed to send test message: {ex}",
                    level="WARNING",
                )
            else:
                items_count += 1
        if items_count:
            self.message_user(
                request, f"Submitted {items_count} successful test message(s)."
            )

    if settings.DEBUG:

        @admin.action(description="Resend mails for selected configurations")
        def resent_mails(self, request, queryset):
            items_count = 0
            for obj in queryset:
                obj.mails_sent.clear()
                new_mails_qs = obj.new_mails_queryset()
                for mail in new_mails_qs:
                    obj.send_mail(mail, timeout=MAILRELAY_DISCORD_USER_TIMEOUT)
                items_count += 1
            self.message_user(
                request,
                f"Resending {new_mails_qs.count()} mails for {items_count} config(s).",
            )


if settings.DEBUG:

    @admin.register(DiscordChannel)
    class DiscordChannelAdmin(admin.ModelAdmin):
        list_display = ("id", "name", "category")
        list_display_links = None
        list_select_related = True
        search_fields = ("name",)
        ordering = ("name",)

        def has_add_permission(self, *args, **kwargs) -> bool:
            return False

        def has_change_permission(self, *args, **kwargs) -> bool:
            return False

    @admin.register(DiscordCategory)
    class DiscordCategoryAdmin(admin.ModelAdmin):
        list_display = ("id", "name")
        list_display_links = None
        search_fields = ("name",)
        ordering = ("name",)

        def has_add_permission(self, *args, **kwargs) -> bool:
            return False

        def has_change_permission(self, *args, **kwargs) -> bool:
            return False
