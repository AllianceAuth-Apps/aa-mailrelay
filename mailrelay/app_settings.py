from app_utils.django import clean_setting

MAILRELAY_OLDEST_MAIL_HOURS = clean_setting("MAILRELAY_OLDEST_MAIL_HOURS", 2)
"""Oldest mail to be forwarded in hours."""

MAILRELAY_RELAY_GRACE_MINUTES = clean_setting("MAILRELAY_RELAY_GRACE_MINUTES", 30)
"""Max time in minutes since last successful relay before service is reported as down."""
