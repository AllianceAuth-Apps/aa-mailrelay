from django.contrib import admin

from .models import DiscordChannel, RelayConfig


@admin.register(RelayConfig)
class RelayConfigAdmin(admin.ModelAdmin):
    list_display = ("__str__", "character", "_channels", "is_enabled")

    def _channels(self, obj) -> str:
        return list(obj.channels.order_by("name").values_list("name", flat=True))

    actions = ["send_new_mails"]

    def send_new_mails(self, request, queryset):
        for obj in queryset:
            obj.send_new_mails()


@admin.register(DiscordChannel)
class DiscordChannelAdmin(admin.ModelAdmin):
    ...
