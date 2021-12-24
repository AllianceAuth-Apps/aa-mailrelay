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
    """Forward new mails from all active configs."""
    for config in RelayConfig.objects.filter(is_enabled=True):
        if not config.channels.exists():
            logger.warning("No channels configured for config %s", config)
            continue
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
    """Forward new mails from one config."""
    config = RelayConfig.objects.select_related(
        "character", "character__character_ownership__character"
    ).get(pk=config_pk)
    if not config.new_mails_queryset().exists():
        logger.info("No new mails to forward.")
        return
    for channel_pk in config.channels.values_list("pk", flat=True):
        forward_new_mails_to_channel.delay(config_pk=config_pk, channel_pk=channel_pk)


@shared_task
def forward_new_mails_to_channel(config_pk, channel_pk):
    """Forward new mails from one config to one channel."""
    config = RelayConfig.objects.select_related(
        "character", "character__character_ownership__character"
    ).get(pk=config_pk)
    new_mails_qs = config.new_mails_queryset()
    channel = config.channels.get(pk=channel_pk)
    logger.info("Forwarding %s eve mails to channel: %s", new_mails_qs.count(), channel)
    chain(
        [
            forward_mail_to_channel.si(
                config_pk=config_pk, mail_pk=mail.pk, channel_pk=channel_pk
            )
            for mail in new_mails_qs.order_by("timestamp")
        ]
    ).delay()


@shared_task
def forward_mail_to_channel(config_pk, mail_pk, channel_pk):
    """Forward one mail to one channel."""
    config = RelayConfig.objects.select_related("character").get(pk=config_pk)
    mail = config.character.mails.get(pk=mail_pk)
    channel = config.channels.get(pk=channel_pk)
    config.send_mail(mail, channel)
