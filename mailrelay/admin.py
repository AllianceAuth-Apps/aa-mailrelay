from collections import defaultdict

from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html

from . import __title__
from .core.discord import create_channel_message
from .models import DiscordCategory, DiscordChannel, RelayConfig


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
        "last_relay_at",
        "_is_service_up",
    )

    actions = ["send_test_message"]

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
        for obj in queryset:
            create_channel_message(
                channel_id=obj.discord_channel.id,
                content=f"Test message from {__title__}",
            )
            items_count += 1
        self.message_user(request, f"Submitted {items_count} test message(s).")


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
