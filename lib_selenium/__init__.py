import functools
import logging
import os
import pickle
import sys
import time
from pathlib import Path

from .browser import get_browser
from .lib_config import get_config, get_logging_options, normalize_path
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
    This is a workaround for killing orphaned processes
    that are not killed when the browser is manually closed.
    """
    if sys.platform == "win32":
        os.system("taskkill /im chromedriver.exe /f")
    else:
        os.system("pkill -f chromedriver")


if not QUIT_WHEN_DONE:
    kill_orphaned_processes()
browser = get_browser()


def save_session():
    """Save the current session to a file. This will also save the current URL."""
    cookies = browser.get_cookies()
    cookies.insert(0, {"url": browser.current_url})
    pickle.dump(cookies, open(CONFIG["Browser"]["session_path"], "wb"))


def restore_session():
    """Restore the session from a file. This will also restore the current URL."""
    try:
        cookies = pickle.load(open(CONFIG["Browser"]["session_path"], "rb"))
        # Cannot set cookies for a domain that is not the current domain.
        browser.get(cookies.pop(0)["url"])
        for cookie in cookies:
            browser.add_cookie(cookie)
        browser.refresh()
    except FileNotFoundError:
        logger.error("Session file not found.")


def go(url):
    """Go to a URL."""
    browser.get(url)


def refresh():
    """Refresh the current page."""
    browser.refresh()


def back():
    """Go back to the previous page."""
    browser.back()


def forward():
    """Go forward to the next page."""
    browser.forward()


def save_screenshot():
    """Save a screenshot of the current page."""
    if not (screenshots_path := CONFIG["Browser"].get("screenshots_path")):
        raise ValueError("Screenshots path not set in config.")
    if not Path(screenshots_path).exists():
        Path(screenshots_path).mkdir(parents=True)
    filename = str(Path(screenshots_path) / Path(f"screenshot_{time.time()}.png"))
    browser.save_screenshot(filename)
    logger.info(f"Screenshot saved to {filename}")


__all__ = [
    "QUIT_WHEN_DONE",
    "back",
    "browser",
    "forward",
    "go",
    "refresh",
    "restore_session",
    "save_screenshot",
    "save_session",
    "timer",
]
