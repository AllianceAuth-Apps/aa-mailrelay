from django.contrib import admin

from .models import DiscordChannel, RelayConfig


@admin.register(RelayConfig)
class RelayConfigAdmin(admin.ModelAdmin):
    actions = ["send_new_mails"]

    def send_new_mails(self, request, queryset):
        for obj in queryset:
            obj.send_new_mails()


@admin.register(DiscordChannel)
class DiscordChannelAdmin(admin.ModelAdmin):
    ...
