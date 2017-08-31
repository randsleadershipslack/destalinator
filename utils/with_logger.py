import logging


class WithLogger(object):
    @property
    def logger(self):
        return logging.getLogger(type(self).__name__)
