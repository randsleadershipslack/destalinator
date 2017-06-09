import codecs
import logging
import os


def get_local_file_content(file_name):
    """Read the contents of `file_name` into a unicode string, return the unicode string."""
    f = codecs.open(file_name, encoding='utf-8')
    ret = f.read().strip()
    f.close()
    return ret


def set_up_logger(logger, log_level_env_var=None, log_to_slack_env_var=None, log_channel=None, default_level='INFO'):
    """
    Sets up a handler and formatter on a given `logging.Logger` object.

    * `log_level_env_var` - Grabs logging level from this ENV var. Possible values are standard: "debug", "error", etc.
    * `log_to_slack_env_var` - FUTURE - Will point to an ENV var that indicates whether to log to a Slack channel.
    * `log_channel` - FUTURE - Will indicate the name of the Slack channel to which we'll send logs.
    * `default_level` - The default log level if one is not set in the environment.
    """
    logger.setLevel(getattr(logging, os.getenv(log_level_env_var, default_level).upper(), getattr(logging, default_level)))
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
