from unittest.mock import patch

from django.test import RequestFactory

from app_utils.testing import NoSocketsTestCase

from ..core.discord import DiscordProxyFetchingChannelsFailed
from ..views import admin_update_discord_channels
from .data_factory import create_superuser

VIEWS_PATH = "mailrelay.views"


@patch(VIEWS_PATH + ".DiscordChannel.objects.sync")
@patch(VIEWS_PATH + ".messages")
class TestViews(NoSocketsTestCase):
    def test_should_post_success_message(self, mock_messages, mock_sync):
        # given
        mock_sync.return_value = 3
        factory = RequestFactory()
        request = factory.get("/mailrelay/admin_update_discord_channels/")
        request.user = create_superuser(username="Clark Kent")
        # when
        response = admin_update_discord_channels(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.success.called)

    def test_should_post_error_message(self, mock_messages, mock_sync):
        # given
        mock_sync.side_effect = DiscordProxyFetchingChannelsFailed
        factory = RequestFactory()
        request = factory.get("/mailrelay/admin_update_discord_channels/")
        request.user = create_superuser(username="Clark Kent")
        # when
        response = admin_update_discord_channels(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.error.called)
