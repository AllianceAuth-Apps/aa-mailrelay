from django.conf import settings

# put your app settings here


MAILRELAY_SETTING_ONE = getattr(settings, "MAILRELAY_SETTING_ONE", None)
