import logging
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


def setup_logging(path, level, log_exceptions, display_stdout, mode):
    level = LOGGING_LEVEL.get(level.lower(), logging.INFO)
    handlers = [logging.FileHandler(path, mode=mode)]

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
        logger = logging.getLogger(__name__)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    if log_exceptions:
        sys.excepthook = handle_exception
