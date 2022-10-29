import logging
import os
import sys

LOGGING_LEVEL = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "fatal": logging.CRITICAL,
}

LOGGING_MODES = {
    "append": "a",
    "write": "w",
}


def get_logging_options(logging_config):
    """Return logging options from config."""

    log_path = logging_config.get("log_path")
    level = logging_config.get("level", "info")
    log_exceptions = logging_config.get("log_exceptions", True)
    display_stdout = logging_config.get("display_stdout", True)
    mode = logging_config.get("mode", "a")
    return log_path, level, log_exceptions, display_stdout, mode


def setup_logging(log_path, level, log_exceptions, display_stdout, mode):
    """Setup logging to file and/or stdout."""

    if not log_path:
        return  # No logging.

    # Ensure directory structure.
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    level = LOGGING_LEVEL.get(level.lower(), logging.INFO)
    mode = LOGGING_MODES.get(mode.lower())
    handlers = [logging.FileHandler(log_path, mode=mode)]

    if display_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        handlers.append(stdout_handler)

    logging.basicConfig(
        level=level,
        format="%(asctime)s::%(levelname)s::%(module)s::%(funcName)s::%(message)s",
        handlers=handlers,
    )

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Log uncaught exceptions."""

        logger = logging.getLogger(__name__)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    if log_exceptions:
        sys.excepthook = handle_exception
