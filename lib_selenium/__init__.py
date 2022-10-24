import functools
import logging
import time

from .lib_config import get_config, get_logging_options
from .lib_logging import setup_logging

CONFIG = get_config()
setup_logging(*get_logging_options(CONFIG))
logger = logging.getLogger(__name__)


def timer(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        logger.info(f"{func.__name__}::{elapsed_time:0.5f} seconds")
        return value

    return wrapped


__all__ = [
    "timer",
]
