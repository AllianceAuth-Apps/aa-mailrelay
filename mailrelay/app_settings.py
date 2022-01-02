from app_utils.django import clean_setting

MAILRELAY_DISCORD_TASK_TIMEOUT = clean_setting("MAILRELAY_DISCORD_TASK_TIMEOUT", 60)
"""Timeout for asynchronous Discord requests in seconds."""

MAILRELAY_DISCORD_USER_TIMEOUT = clean_setting("MAILRELAY_DISCORD_USER_TIMEOUT", 30)
"""Timeout for user facing Discord requests in seconds."""

MAILRELAY_OLDEST_MAIL_HOURS = clean_setting("MAILRELAY_OLDEST_MAIL_HOURS", 2)
"""Oldest mail to be forwarded in hours."""

MAILRELAY_RELAY_GRACE_MINUTES = clean_setting("MAILRELAY_RELAY_GRACE_MINUTES", 30)
"""Max time in minutes since last successful relay before service is reported as down."""
