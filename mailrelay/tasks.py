from celery import chain, shared_task
from memberaudit.models import Character
from memberaudit.tasks import (
    update_character_mail_bodies,
    update_character_mail_headers,
    update_character_mail_labels,
    update_character_mailing_lists,
    update_unresolved_eve_entities,
)

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .models import RelayConfig

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@shared_task
def forward_new_mails():
    for config in RelayConfig.objects.filter(is_enabled=True):
        chain(
            [
                update_character_mailing_lists.si(
                    config.character.pk, force_update=True
                ),
                update_character_mail_labels.si(config.character.pk, force_update=True),
                update_character_mail_headers.si(
                    config.character.pk, force_update=True
                ),
                update_character_mail_bodies.si(config.character.pk),
                update_unresolved_eve_entities.si(
                    config.character.pk, Character.UpdateSection.MAILS
                ),
                forward_new_mails_for_config.si(config.pk),
            ]
        ).delay()


@shared_task
def forward_new_mails_for_config(config_pk):
    config = RelayConfig.objects.select_related(
        "character", "character__character_ownership__character"
    ).get(pk=config_pk)
    config.send_new_mails()
