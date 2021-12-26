from django.conf import settings
from django.contrib import admin
from django.db.models.functions import Lower
from django.utils.html import format_html

from . import __title__
from .core.discord import create_channel_message
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

    actions = ["send_test_message"]

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

    autocomplete_fields = ["character"]
    fields = (
        "character",
        "mail_category",
        "discord_channel",
        "ping_type",
        "is_enabled",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "discord_channel":
            kwargs["queryset"] = DiscordChannel.objects.order_by(Lower("name"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
