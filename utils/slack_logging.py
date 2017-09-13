import logging

from config import get_config, WithLogger


class SlackHandler(logging.Handler, WithLogger):
    """
    A logging.Handler subclass for logging messages into a Slack channel.

    See also: https://docs.python.org/3/library/logging.html#handler-objects
    """
    def __init__(self, slackbot, level):
        """
        `slackbot` is an initialized Slackbot() object
        `log_channel` is the name of a channel that should receive log messages
        `level` is the log level to use for logging to the Slack channel
        """
        super(self.__class__, self).__init__(level)  # pylint: disable=E1003
        self.slackbot = slackbot

    def emit(self, record):
        """Do whatever it takes to actually log the specified logging record."""
        self.slackbot.say(self.config.log_channel, record.getMessage())


def set_up_slack_logger(slackbot=None):
    """
    Sets up a handler and formatter on a given `logging.Logger` object.

    * `log_level_env_var` - Grabs logging level from this ENV var. Possible values are standard: "debug", "error", etc.
    * `log_to_slack_env_var` - Points to an ENV var that indicates whether to log to a Slack channel.
    * `log_channel` - Indicates the name of the Slack channel to which we'll send logs.
    * `default_level` - The default log level if one is not set in the environment.
    * `slackbot` - A slackbot.Slackbot() object ready to send messages to a Slack channel.
    """
    logger = logging.getLogger()

    if logger.handlers:
        # We've likely already ran through the rest of this method:
        return

    _config = get_config()

    slack_log_level = getattr(logging, _config.log_level.upper(), logging.INFO)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    if _config.log_to_channel and _config.log_channel and slackbot:
        logger.debug("Logging to slack channel: %s", _config.log_channel)
        slack_handler = SlackHandler(slackbot=slackbot, level=slack_log_level)
        slack_handler.setFormatter(formatter)
        logger.addHandler(slack_handler)
