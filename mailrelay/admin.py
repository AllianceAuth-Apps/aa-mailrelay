from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from .models import DiscordChannel, RelayConfig


@admin.register(RelayConfig)
class RelayConfigAdmin(admin.ModelAdmin):
    change_list_template = "admin/mailrelay/relayconfig/change_list.html"
    list_display = (
        "__str__",
        "character",
        "_channel",
        "is_enabled",
        "last_relay_at",
        "_is_service_up",
    )

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

    autocomplete_fields = ["character"]
    fields = (
        "character",
        "mail_category",
        "discord_channel",
        "ping_type",
        "is_enabled",
    )


if settings.DEBUG:

    @admin.register(DiscordChannel)
    class DiscordChannelAdmin(admin.ModelAdmin):
        list_display = ("id", "name")
        list_display_links = None
        search_fields = ("name",)
        ordering = ("name",)

        def has_add_permission(self, *args, **kwargs) -> bool:
            return False

        def has_change_permission(self, *args, **kwargs) -> bool:
            return False
