from unittest.mock import Mock, patch

from app_utils.testing import NoSocketsTestCase

from ..core.discord import fetch_channels
from .data_factory import create_discordproxy_channel

MODULE_PATH = "mailrelay.core.discord"


@patch(MODULE_PATH + ".DiscordApiStub")
@patch(MODULE_PATH + ".grpc.insecure_channel", spec=True)
class TestFetchChannels(NoSocketsTestCase):
    def test_should_return_channels(self, mock_insecure_channel, mock_DiscordApiStub):
        response = Mock()
        response.channels = [
            create_discordproxy_channel(id=1, name="dummy-1"),
            create_discordproxy_channel(id=2, name="dummy-2"),
        ]
        mock_DiscordApiStub.return_value.GetGuildChannels.return_value = response
        # when
        result = fetch_channels()
        # then
        channel_ids = {obj.id for obj in result}
        self.assertSetEqual(channel_ids, {1, 2})
