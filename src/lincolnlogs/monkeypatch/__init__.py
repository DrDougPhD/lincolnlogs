import logging
from . import deprecation


def apply():
    # Monkey patch the Logger class to have more convenience methods.
    logging.Logger.deprecated = deprecation.log
