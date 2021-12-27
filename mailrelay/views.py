from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .core.discord_client import DiscordError
from .models import DiscordChannel


@login_required
@staff_member_required
def admin_update_discord_channels(request):
    try:
        channels_count = DiscordChannel.objects.sync()
        messages.success(
            request, f"Successfully updated {channels_count} channels from Discord."
        )
    except DiscordError as ex:
        messages.warning(request, f"Failed to fetch channels from Discord: {ex}")
    return redirect("admin:mailrelay_relayconfig_changelist")
