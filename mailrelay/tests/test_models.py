import datetime as dt
from unittest.mock import patch

from memberaudit.tests import add_memberaudit_character_to_user
from pytz import utc

from django.test import TestCase

from app_utils.testing import create_fake_user

from ..models import RelayConfig
from .helpers import (
    create_character_mail,
    create_eve_entities_from_evecharacter,
    create_eve_entity,
    create_relay_config,
)

MODULE_PATH = "mailrelay.models"


class TestRelayConfig(TestCase):
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
        with patch(MODULE_PATH + ".now") as mock_now:
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
        with patch(MODULE_PATH + ".now") as mock_now:
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
        with patch(MODULE_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 24, 12, 30, tzinfo=utc)
            result = config.new_mails_queryset()
        # then
        self.assertSetEqual(
            {corporation_mail.pk, personal_mail.pk, alliance_mail.pk},
            set(result.values_list("pk", flat=True)),
        )

    @patch(MODULE_PATH + ".send_messages_to_channel")
    def test_should_send_mail(self, mock_send_messages_to_channel):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        mail = create_character_mail(character=character, sender_id=1002)
        config = create_relay_config(character=character)
        # when
        result = config.send_mail(mail, config.channels.first())
        # then
        self.assertTrue(result)
        self.assertTrue(mock_send_messages_to_channel.called)
