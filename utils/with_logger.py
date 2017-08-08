import logging
import os


def set_up_log_level():
    logger = logging.getLogger()
    log_level_env_var = 'DESTALINATOR_LOG_LEVEL'
    default_level='INFO'
    log_level = getattr(logging, os.getenv(log_level_env_var, default_level).upper(), getattr(logging, default_level))
    logger.setLevel(log_level)


class WithLogger(object):
    @property
    def logger(self):
        return logging.getLogger(__name__)
