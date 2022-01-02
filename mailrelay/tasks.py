from celery import chain, shared_task
from discordproxy.exceptions import DiscordProxyException
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
from .app_settings import MAILRELAY_DISCORD_TASK_TIMEOUT
from .models import RelayConfig

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@shared_task
def forward_new_mails():
    """Forward new mails from all active configs."""
    for config in RelayConfig.objects.filter(is_enabled=True):
        if not config.discord_channel:
            logger.warning("No channel configured for config %s", config)
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
    new_mails_qs = config.new_mails_queryset()
    if not new_mails_qs.exists():
        config.record_service_run()
        logger.debug("No new mails to forward.")
        return
    logger.info(
        "Forwarding %s eve mails to channel: %s",
        new_mails_qs.count(),
        config.discord_channel,
    )
    my_tasks = [
        forward_mail_to_discord.si(config_pk=config_pk, mail_pk=mail.pk)
        for mail in new_mails_qs.order_by("timestamp")
    ]
    my_tasks.append(record_service_run.si(config_pk))
    chain(my_tasks).delay()


@shared_task
def forward_mail_to_discord(config_pk, mail_pk):
    """Forward one mail to Discord."""
    config = RelayConfig.objects.select_related("character", "discord_channel").get(
        pk=config_pk
    )
    mail = config.character.mails.get(pk=mail_pk)
    try:
        config.send_mail(mail=mail, timeout=MAILRELAY_DISCORD_TASK_TIMEOUT)
    except DiscordProxyException as ex:
        logger.error(
            "%s: Failed to send mail %s due to error from Discord Proxy. Will try again later: %s",
            config,
            mail,
            ex,
        )


@shared_task
def record_service_run(config_pk):
    """Record completion of successful relay."""
    config = RelayConfig.objects.get(pk=config_pk)
    config.record_service_run()
