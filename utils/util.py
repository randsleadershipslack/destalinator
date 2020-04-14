import re


def ignore_channel(config, channel_name):
    """Return True if `channel_name` is a channel we should ignore based on config settings."""
    if channel_name in config.ignore_channels:
        return True
    for pat in config.ignore_channel_patterns:
        if re.search(pat, channel_name):
            return True
    return False