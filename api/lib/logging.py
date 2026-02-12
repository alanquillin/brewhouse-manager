# pylint: disable=unused-wildcard-import

import logging
import sys
from logging import *  # pylint: disable=wildcard-import

from lib.config import Config

DEFAULT_LOG_FMT = "%(levelname)s:     %(asctime)-15s [%(name)s]: %(message)s"
DEFAULT_COLORED_LOG_FMT = "%(log_color)s%(levelname)s:     %(asctime)-15s [%(name)s]:%(reset)s %(message)s"
DEFAULT_JSON_LOG_FMT = "%(asctime)s %(levelname)s %(name)s %(message)s"

DEFAULT_LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


def get_log_level(log_level_str: str, default_level=INFO) -> int:
    return getattr(logging, log_level_str.upper(), default_level)


def set_log_level(logging_level: int) -> None:
    logging.getLogger().setLevel(logging_level)


def get_def_log_level(config, log_levels=None) -> str:
    if not log_levels:
        log_levels = config.get("logging.levels", {})
    default_log_level_fallback = log_levels.pop("default", "INFO")

    return config.get("log_level", config.get("logging.level", default_log_level_fallback))


def _create_formatter(config, fmt=DEFAULT_LOG_FMT):
    use_json = config.get("logging.json", False)
    use_color = config.get("logging.colored", True)

    if use_json:
        from pythonjsonlogger import json as jsonlogger

        return jsonlogger.JsonFormatter(
            fmt=DEFAULT_JSON_LOG_FMT,
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )

    if use_color:
        try:
            import colorlog  # pylint: disable=import-outside-toplevel

            return colorlog.ColoredFormatter(
                fmt=DEFAULT_COLORED_LOG_FMT,
                log_colors=DEFAULT_LOG_COLORS,
            )
        except ImportError:
            pass

    return Formatter(fmt=fmt)


def _enforce_root_propagation():
    """Strip handlers from all non-root loggers and ensure they propagate to root.

    This forces every logger (asyncio, uvicorn, sqlalchemy, etc.) to flow
    through the single root handler so formatting stays consistent.
    """
    manager = logging.Logger.manager
    for name in list(manager.loggerDict):
        logger = manager.loggerDict[name]
        if isinstance(logger, logging.Logger):
            logger.handlers.clear()
            logger.propagate = True


def init(config=None, fmt=DEFAULT_LOG_FMT):
    if not config:
        config = Config()

    log_levels = config.get("logging.levels", {})
    log_level = get_log_level(get_def_log_level(config, log_levels))

    formatter = _create_formatter(config, fmt)

    root_logger = getLogger()
    root_logger.setLevel(log_level)

    # Replace all root handlers with a single consistently-formatted handler
    root_logger.handlers.clear()
    handler = StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Force all existing loggers to propagate through root
    _enforce_root_propagation()

    # Route Python warnings (e.g. SAWarning) through the logging system
    # so they use the same formatter instead of writing raw text to stderr
    logging.captureWarnings(True)

    for l, level in log_levels.items():
        root_logger.debug("Setting log level for %s to %s", l, level)
        getLogger(l).setLevel(get_log_level(level))

    root_logger.debug("logging initialization complete.")
