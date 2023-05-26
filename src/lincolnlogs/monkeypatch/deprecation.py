import logging


def log(logger: logging.Logger, message: str):
    logger.warning(f'DEPRECATED: {message}')
