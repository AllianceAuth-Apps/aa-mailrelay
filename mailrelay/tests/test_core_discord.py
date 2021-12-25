from unittest.mock import Mock, patch

from discordproxy.discord_api_pb2 import Channel, Embed

from app_utils.testing import NoSocketsTestCase

from ..core.discord import (
    DiscordMessage,
    DiscordProxyFetchingChannelsFailed,
    DiscordProxySendingMessagesFailed,
    fetch_text_channels,
    send_messages_to_channels,
)
from .data_factory import create_discordproxy_channel, create_rpc_error

MODULE_PATH = "mailrelay.core.discord"


@patch(MODULE_PATH + ".DiscordApiStub")
@patch(MODULE_PATH + ".grpc.insecure_channel", spec=True)
class TestFetchChannels(NoSocketsTestCase):
    def test_should_return_text_channels(
        self, mock_insecure_channel, mock_DiscordApiStub
    ):
        # given
        response = Mock()
        response.channels = [
            create_discordproxy_channel(
                id=1, name="dummy-1", type=Channel.Type.GUILD_TEXT
            ),
            create_discordproxy_channel(
                id=2, name="dummy-2", type=Channel.Type.GUILD_TEXT
            ),
            create_discordproxy_channel(
                id=2, name="dummy-2", type=Channel.Type.GUILD_VOICE
            ),
        ]
        mock_DiscordApiStub.return_value.GetGuildChannels.return_value = response
        # when
        result = fetch_text_channels()
        # then
        channel_ids = {obj.id for obj in result}
        self.assertSetEqual(channel_ids, {1, 2})

    def test_should_raise_exception(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        error = create_rpc_error()
        mock_DiscordApiStub.return_value.GetGuildChannels.side_effect = error
        # when/then
        with self.assertRaises(DiscordProxyFetchingChannelsFailed):
            fetch_text_channels()


@patch(MODULE_PATH + ".DiscordApiStub")
@patch(MODULE_PATH + ".grpc.insecure_channel", spec=True)
class TestSendMessagesToChannels(NoSocketsTestCase):
    def test_should_return_channels(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        messages = [
            DiscordMessage(
                channel_id=1, content="alpha", embed=Embed(description="test")
            )
        ]
        # when
        send_messages_to_channels(messages)
        # then
        pass

    def test_should_raise_error(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        error = create_rpc_error()
        mock_DiscordApiStub.return_value.SendChannelMessage.side_effect = error
        messages = [
            DiscordMessage(
                channel_id=1, content="alpha", embed=Embed(description="test")
            )
        ]
        # when/then
        with self.assertRaises(DiscordProxySendingMessagesFailed):
            send_messages_to_channels(messages)
