import functools
import logging
import os
import pickle
import sys
import time

from .browser import get_browser
from .lib_config import get_config, get_logging_options
from .lib_logging import setup_logging

CONFIG = get_config()
QUIT_WHEN_DONE = CONFIG["Browser"].get("quit_when_done", True)
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


def kill_orphaned_processes():
    """Kill orphaned chromedriver processes.
    This is a workaround for killing orphaned processes that are not killed when the browser is manually closed.
    """
    if sys.platform == "win32":
        os.system("taskkill /im chromedriver.exe /f")
    else:
        os.system("pkill -f chromedriver")


if not QUIT_WHEN_DONE:
    kill_orphaned_processes()
browser = get_browser()


def save_session():
    pickle.dump(browser.get_cookies(), open(CONFIG["Browser"]["session_path"], "wb"))


def restore_session():
    try:
        for cookie in pickle.load(open(CONFIG["Browser"]["session_path"], "rb")):
            browser.add_cookie(cookie)
    except FileNotFoundError:
        logger.error("Session file not found.")


def go(url):
    browser.get(url)


__all__ = [
    "QUIT_WHEN_DONE",
    "browser",
    "go",
    "restore_session",
    "save_session",
    "timer",
]
