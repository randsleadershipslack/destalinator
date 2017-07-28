import logging

class WithLogger(object):
    @property
    def logger(self):
        return logging.getLogger(__name__)
