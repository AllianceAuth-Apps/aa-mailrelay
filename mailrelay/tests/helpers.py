import datetime as dt

from memberaudit.models import CharacterMail, MailEntity
from pytz import utc

from django.db.models import Max
from eveuniverse.models import EveEntity

from ..models import RelayConfig


def create_eve_entity(**kwargs) -> EveEntity:
    if "category" not in kwargs:
        kwargs["category"] = EveEntity.CATEGORY_CHARACTER
    return EveEntity.objects.create(**kwargs)


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


def create_character_mail(sender_id, recipient_ids=None, **kwargs) -> CharacterMail:
    if "timestamp" not in kwargs:
        kwargs["timestamp"] = dt.datetime(2021, 12, 24, 12, 15, tzinfo=utc)
    if not recipient_ids:
        recipient_ids = []
    if "character" not in kwargs:
        raise ValueError("character parameter not provided")
    character = kwargs["character"]
    sender, _ = MailEntity.objects.update_or_create_from_eve_entity_id(id=sender_id)
    mail_id = _generate_mail_id()
    kwargs.update(
        {
            "subject": f"subject #{mail_id}",
            "body": f"body #{mail_id}",
            "is_read": False,
            "mail_id": mail_id,
            "sender": sender,
        }
    )
    mail = CharacterMail.objects.create(**kwargs)
    recipient_ids += [character.character_ownership.character.character_id]
    recipient_objs = [
        MailEntity.objects.update_or_create_from_eve_entity_id(id=recipient_id)[0]
        for recipient_id in recipient_ids
    ]
    mail.recipients.add(*recipient_objs)
    return mail


def _generate_mail_id() -> int:
    mail_id = CharacterMail.objects.aggregate(Max("mail_id"))["mail_id__max"]
    if not mail_id:
        mail_id = 1
    else:
        mail_id += 1
    return mail_id


def create_relay_config(**kwargs):
    if "mail_category" not in kwargs:
        kwargs["mail_category"] = RelayConfig.MailCategory.ALL
    return RelayConfig.objects.create(**kwargs)
