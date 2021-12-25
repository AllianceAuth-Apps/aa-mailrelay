import datetime as dt
from unittest.mock import patch

from memberaudit.tests import add_memberaudit_character_to_user
from pytz import utc

from app_utils.testing import NoSocketsTestCase, create_fake_user

from ..models import DiscordChannel, RelayConfig
from .data_factory import (
    create_character_mail,
    create_discord_channel,
    create_discordproxy_channel,
    create_eve_entities_from_evecharacter,
    create_eve_entity,
    create_relay_config,
)

MODELS_PATH = "mailrelay.models"
MANAGERS_PATH = "mailrelay.managers"


class TestRelayConfig(NoSocketsTestCase):
    def test_should_return_corporation_mails_only(self):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        corporation_mail = create_character_mail(
            character=character, sender_id=1002, recipient_ids=[2001]
        )
        create_character_mail(character=character, sender_id=1002)
        create_character_mail(character=character, sender_id=1002, recipient_ids=[3001])
        config = create_relay_config(
            character=character, mail_category=RelayConfig.MailCategory.CORPORATION
        )
        # when
        with patch(MODELS_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 24, 12, 30, tzinfo=utc)
            result = config.new_mails_queryset()
        # then
        self.assertSetEqual(
            {corporation_mail.pk}, set(result.values_list("pk", flat=True))
        )

    def test_should_return_alliance_mails_only(self):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        alliance_mail = create_character_mail(
            character=character, sender_id=1002, recipient_ids=[3001]
        )
        create_character_mail(character=character, sender_id=1002)
        create_character_mail(character=character, sender_id=1002, recipient_ids=[2001])
        config = create_relay_config(
            character=character, mail_category=RelayConfig.MailCategory.ALLIANCE
        )
        # when
        with patch(MODELS_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 24, 12, 30, tzinfo=utc)
            result = config.new_mails_queryset()
        # then
        self.assertSetEqual(
            {alliance_mail.pk}, set(result.values_list("pk", flat=True))
        )

    def test_should_return_all_mails(self):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        corporation_mail = create_character_mail(
            character=character, sender_id=1002, recipient_ids=[2001]
        )
        personal_mail = create_character_mail(character=character, sender_id=1002)
        alliance_mail = create_character_mail(
            character=character, sender_id=1002, recipient_ids=[3001]
        )
        config = create_relay_config(
            character=character, mail_category=RelayConfig.MailCategory.ALL
        )
        # when
        with patch(MODELS_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 24, 12, 30, tzinfo=utc)
            result = config.new_mails_queryset()
        # then
        self.assertSetEqual(
            {corporation_mail.pk, personal_mail.pk, alliance_mail.pk},
            set(result.values_list("pk", flat=True)),
        )

    @patch(MODELS_PATH + ".send_messages_to_channel")
    def test_should_send_mail(self, mock_send_messages_to_channel):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        mail = create_character_mail(character=character, sender_id=1002)
        config = create_relay_config(character=character)
        # when
        config.send_mail(mail, config.channels.first())
        # then
        self.assertTrue(mock_send_messages_to_channel.called)


@patch(MANAGERS_PATH + ".fetch_text_channels", spec=True)
class TestDiscordChannelManager(NoSocketsTestCase):
    def test_should_create_new_channels_from_scratch(self, mock_fetch_text_channels):
        # given
        mock_fetch_text_channels.return_value = [
            create_discordproxy_channel(id=1, name="alpha"),
            create_discordproxy_channel(id=2, name="bravo"),
        ]
        # when
        result = DiscordChannel.objects.sync()
        # then
        self.assertEqual(result, 2)
        self.assertEqual(DiscordChannel.objects.count(), 2)
        obj = DiscordChannel.objects.get(id=1)
        self.assertEqual(obj.name, "alpha")
        obj = DiscordChannel.objects.get(id=2)
        self.assertEqual(obj.name, "bravo")

    def test_should_update_existing_channels(self, mock_fetch_text_channels):
        # given
        mock_fetch_text_channels.return_value = [
            create_discordproxy_channel(id=1, name="alpha"),
            create_discordproxy_channel(id=2, name="bravo"),
        ]
        create_discord_channel(id=1, name="update-me")
        # when
        result = DiscordChannel.objects.sync()
        # then
        self.assertEqual(result, 2)
        self.assertEqual(DiscordChannel.objects.count(), 2)
        obj = DiscordChannel.objects.get(id=1)
        self.assertEqual(obj.name, "alpha")
        obj = DiscordChannel.objects.get(id=2)
        self.assertEqual(obj.name, "bravo")

    def test_should_remove_obsolete_channels(self, mock_fetch_text_channels):
        # given
        mock_fetch_text_channels.return_value = [
            create_discordproxy_channel(id=1, name="alpha"),
            create_discordproxy_channel(id=2, name="bravo"),
        ]
        create_discord_channel(id=3, name="delete-me")
        # when
        result = DiscordChannel.objects.sync()
        # then
        self.assertEqual(result, 2)
        self.assertEqual(DiscordChannel.objects.count(), 2)
        obj = DiscordChannel.objects.get(id=1)
        self.assertEqual(obj.name, "alpha")
        obj = DiscordChannel.objects.get(id=2)
        self.assertEqual(obj.name, "bravo")
