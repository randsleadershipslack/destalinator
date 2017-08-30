import logging

# No logging for tests:
logging.getLogger().addHandler(logging.NullHandler())
