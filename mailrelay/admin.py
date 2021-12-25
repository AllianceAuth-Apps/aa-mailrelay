from django.conf import settings
from django.contrib import admin
from django.db.models.functions import Lower
from django.utils.html import format_html

from .models import DiscordChannel, RelayConfig


@admin.register(RelayConfig)
class RelayConfigAdmin(admin.ModelAdmin):
    change_list_template = "admin/mailrelay/relayconfig/change_list.html"
    list_display = ("__str__", "character", "_channels", "is_enabled")

    def _channels(self, obj) -> str:
        channels = list(obj.channels.order_by("name").values_list("name", flat=True))
        if not channels:
            return format_html(
                '<span style="color:red;"><b>Error: No channel configured</b></span>'
            )
        return channels

    filter_horizontal = ("channels",)
    autocomplete_fields = ["character"]
    fields = ("character", "mail_category", "channels", "ping_type", "is_enabled")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """overriding this formfield to have sorted lists in the form"""
        if db_field.name == "channels":
            kwargs["queryset"] = DiscordChannel.objects.all().order_by(Lower("name"))
        return super().formfield_for_manytomany(db_field, request, **kwargs)


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
