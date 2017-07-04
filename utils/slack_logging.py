import logging
import os

from config import Config


class SlackHandler(logging.Handler):
    """
    A logging.Handler subclass for logging messages into a Slack channel.

    See also: https://docs.python.org/3/library/logging.html#handler-objects
    """
    def __init__(self, slackbot, log_channel, level):
        """
        `slackbot` is an initialized Slackbot() object
        `log_channel` is the name of a channel that should receive log messages
        `level` is the log level to use for logging to the Slack channel
        """
        super(self.__class__, self).__init__(level)  # pylint: disable=E1003
        self.slackbot = slackbot
        self.log_channel = log_channel

    def emit(self, record):
        """Do whatever it takes to actually log the specified logging record."""
        self.slackbot.say(self.log_channel, record.getMessage())

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

    config = Config()
    log_level_env_var = 'DESTALINATOR_LOG_LEVEL'
    log_to_slack_env_var = 'DESTALINATOR_LOG_TO_CHANNEL'

    default_level='INFO'
    slack_log_level = getattr(logging, os.getenv(log_level_env_var, default_level).upper(), getattr(logging, default_level))

    has_log_to_slack_env_var = os.getenv(config.output_debug_env_varname) or os.getenv(log_to_slack_env_var)

    log_channel = config.log_channel

    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')


    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    logger.addHandler(stream_handler)

    if has_log_to_slack_env_var and log_channel and slackbot:
        logger.debug("Logging to slack channel: %s", log_channel)

        slack_handler = SlackHandler(slackbot=slackbot, log_channel=log_channel, level=slack_log_level)
        slack_handler.setFormatter(formatter)
        logger.addHandler(slack_handler)
