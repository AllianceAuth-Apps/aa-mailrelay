import datetime as dt
from unittest.mock import patch

from memberaudit.models import CharacterMail, MailEntity
from memberaudit.tests import add_memberaudit_character_to_user
from pytz import utc

from django.db.models import Max
from django.test import TestCase
from eveuniverse.models import EveEntity

from app_utils.testing import create_fake_user

from ..models import RelayConfig

MODULE_PATH = "mailrelay.models"


def create_eve_entity(**kwargs) -> EveEntity:
    if "category" not in kwargs:
        kwargs["category"] = EveEntity.CATEGORY_CHARACTER
    return EveEntity.objects.get_or_create(**kwargs)[0]


def create_eve_entities_from_evecharacter(character):
    create_eve_entity(
        id=character.character_id,
        name=character.character_name,
        category=EveEntity.CATEGORY_CHARACTER,
    )
    create_eve_entity(
        id=character.corporation_id,
        name=character.corporation_name,
        category=EveEntity.CATEGORY_CORPORATION,
    )
    if character.alliance_id:
        create_eve_entity(
            id=character.alliance_id,
            name=character.alliance_name,
            category=EveEntity.CATEGORY_ALLIANCE,
        )


def create_character_mail(
    character, sender_id, recipient_ids=None, timestamp=None
) -> CharacterMail:
    mail_id = CharacterMail.objects.aggregate(Max("mail_id"))["mail_id__max"]
    if not mail_id:
        mail_id = 1
    else:
        mail_id += 1
    if not timestamp:
        timestamp = dt.datetime(2021, 12, 24, 12, 15, tzinfo=utc)
    if not recipient_ids:
        recipient_ids = []
    recipient_ids += [character.character_ownership.character.character_id]
    sender, _ = MailEntity.objects.update_or_create_from_eve_entity_id(id=sender_id)
    mail = CharacterMail.objects.create(
        character=character,
        mail_id=mail_id,
        sender=sender,
        subject="subject",
        body="body",
        is_read=False,
        timestamp=timestamp,
    )
    recipient_objs = [
        MailEntity.objects.update_or_create_from_eve_entity_id(id=recipient_id)[0]
        for recipient_id in recipient_ids
    ]
    mail.recipients.add(*recipient_objs)
    return mail


def create_relay_config(**kwargs):
    if "mail_category" not in kwargs:
        kwargs["mail_category"] = RelayConfig.MailCategory.CORPORATION
    return RelayConfig.objects.get_or_create(**kwargs)[0]


class TestRelayConfig(TestCase):
    def test_should_return_corporation_mails_only(self):
        # given
        user = create_fake_user(1001, "Bruce Wayne")
        character = add_memberaudit_character_to_user(user, 1001)
        create_eve_entities_from_evecharacter(character.character_ownership.character)
        create_eve_entity(id=1002, name="Peter Parker")
        corporation_mail = create_character_mail(
            character, sender_id=1002, recipient_ids=[2001]
        )
        create_character_mail(character, sender_id=1002)
        create_character_mail(character, sender_id=1002, recipient_ids=[3001])
        config = create_relay_config(character=character)
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
            character, sender_id=1002, recipient_ids=[3001]
        )
        create_character_mail(character, sender_id=1002)
        create_character_mail(character, sender_id=1002, recipient_ids=[2001])
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
