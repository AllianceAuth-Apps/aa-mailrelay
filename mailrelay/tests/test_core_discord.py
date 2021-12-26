from unittest.mock import Mock, patch

from discordproxy.discord_api_pb2 import Channel, Embed

from app_utils.testing import NoSocketsTestCase

from ..core.discord import (
    DiscordError,
    Message,
    create_channel_message,
    get_text_channels,
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
        result = get_text_channels()
        # then
        channel_ids = {obj.id for obj in result}
        self.assertSetEqual(channel_ids, {1, 2})

    def test_should_raise_exception(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        error = create_rpc_error()
        mock_DiscordApiStub.return_value.GetGuildChannels.side_effect = error
        # when/then
        with self.assertRaises(DiscordError):
            get_text_channels()


@patch(MODULE_PATH + ".DiscordApiStub")
@patch(MODULE_PATH + ".grpc.insecure_channel", spec=True)
class TestCreateChannelMessage(NoSocketsTestCase):
    def test_should_return_channels(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        message = Message(
            channel_id=1, content="alpha", embeds=[Embed(description="test")]
        )
        mock_DiscordApiStub.return_value.SendChannelMessage.return_value.message = (
            message
        )
        # when
        result = create_channel_message(
            channel_id=message.channel_id,
            content=message.content,
            embed=message.embeds[0],
        )
        # then
        self.assertEqual(result, message)

    def test_should_raise_error(self, mock_insecure_channel, mock_DiscordApiStub):
        # given
        error = create_rpc_error()
        mock_DiscordApiStub.return_value.SendChannelMessage.side_effect = error
        # when/then
        with self.assertRaises(DiscordError):
            create_channel_message(channel_id=1, content="alpha")

    def test_should_require_content_or_embed(
        self, mock_insecure_channel, mock_DiscordApiStub
    ):
        # when/then
        with self.assertRaises(ValueError):
            create_channel_message(channel_id=1)
