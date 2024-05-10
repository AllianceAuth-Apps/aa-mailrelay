"""Providers for Mail Relay."""

from discordproxy.client import DiscordClient

from .app_settings import MAILRELAY_DISCORDPROXY_TIMEOUT


def create_discordproxy_client() -> DiscordClient:
    """Return client from discordproxy configured for Mail Relay."""
    return DiscordClient(timeout=MAILRELAY_DISCORDPROXY_TIMEOUT)
