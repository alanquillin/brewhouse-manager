# pylint: disable=unused-wildcard-import

import logging
from logging import *  # pylint: disable=wildcard-import

from lib.config import Config

DEFAULT_LOG_FMT = "%(levelname)-8s: %(asctime)-15s [%(name)s]: %(message)s"


def get_log_level(log_level_str, default_level=INFO):
    return getattr(logging, log_level_str.upper(), default_level)


def init(config=None, fmt=DEFAULT_LOG_FMT):
    if not config:
        config = Config()

    log_levels = config.get("logging.levels", {})
    default_log_level_fallback = log_levels.pop("default", "INFO")

    log_level = get_log_level(config.get("log_level", config.get("logging.level", default_log_level_fallback)))

    root_logger = getLogger()
    root_logger.setLevel(log_level)
    if root_logger.handlers:
        for log_handler in root_logger.handlers:
            log_handler.setFormatter(Formatter(fmt=fmt))
    basicConfig(level=log_level, format=fmt)

    for l, level in log_levels.items():
        root_logger.debug("Setting log level for %s to %s", l, level)
        getLogger(l).setLevel(get_log_level(level))

    root_logger.debug("logging initialization complete.")
