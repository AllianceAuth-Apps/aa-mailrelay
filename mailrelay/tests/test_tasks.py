"""
import datetime as dt
from unittest.mock import patch

from memberaudit.tests import add_memberaudit_character_to_user
from pytz import utc

from django.test import override_settings

from app_utils.testing import NoSocketsTestCase, create_fake_user

from ..tasks import forward_new_mails_for_config
from .helpers import (
    create_character_mail,
    create_eve_entities_from_evecharacter,
    create_eve_entity,
    create_relay_config,
)

MODELS_PATH = "mailrelay.modules"
TASKS_PATH = "mailrelay.tasks"


@override_settings(CELERY_ALWAYS_EAGER=True)
class TestForwardNewMails(NoSocketsTestCase):
    def test_should_forward_all_mails(self):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        mail_1 = create_character_mail(
            character=character, sender_id=1002, recipient_ids=[2001]
        )
        mail_2 = create_character_mail(character=character, sender_id=1002)
        config = create_relay_config(character=character)
        # when
        with patch(MODELS_PATH + ".now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 24, 12, 30, tzinfo=utc)
            forward_new_mails_for_config.delay()
        # then
        # self.assertSetEqual(
        #     {corporation_mail.pk}, set(result.values_list("pk", flat=True))
        # )
"""
