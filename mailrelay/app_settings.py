from app_utils.django import clean_setting

MAILRELAY_OLDEST_MAIL_HOURS = clean_setting("MAILRELAY_OLDEST_MAIL_HOURS", 2)
"""Oldest mail to be forwarded in hours."""
