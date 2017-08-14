import logging
import os

log_level_set = False

def set_up_log_level():
    global log_level_set
    if log_level_set:
        return
    log_level_set = True
    logger = logging.getLogger()
    log_level_env_var = 'DESTALINATOR_LOG_LEVEL'
    default_level='INFO'
    log_level = getattr(logging, os.getenv(log_level_env_var, default_level).upper(), getattr(logging, default_level))
    logger.setLevel(log_level)


class WithLogger(object):
    @property
    def logger(self):
        return logging.getLogger(__name__)
