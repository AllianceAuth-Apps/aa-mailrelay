from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import DiscordChannel


@login_required
@staff_member_required
def admin_update_discord_channels(request):
    DiscordChannel.objects.sync()
    return redirect("admin:mailrelay_relayconfig_changelist")
