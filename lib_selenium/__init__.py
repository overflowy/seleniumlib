import functools
import logging
import os
import pickle
import sys
import time
from pathlib import Path

from selenium.common.exceptions import *
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import get_browser
from .lib_config import get_config, get_logging_options, normalize_path
from .lib_logging import setup_logging

CONFIG = get_config()
DEBUG_ON_EXCEPTION = CONFIG["Browser"].get("debug_on_exception", False)
QUIT_WHEN_DONE = CONFIG["Browser"].get("quit_when_done", True)
TIMEOUT = CONFIG["Browser"].get("global_timeout", 5)
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


def element_exists(element, find_by=By.ID):
    """Check if element exists."""
    try:
        browser.find_element(find_by, element)
    except NoSuchElementException:
        return False
    return True


def html():
    """Return the HTML of the current page."""
    return browser.page_source


def page_contains_text(text):
    """Check if page contains text."""
    return text in html()


def _click(element, find_by=By.ID, alias=None):
    """Wait for an element to be available and click it."""
    try:
        WebDriverWait(browser, TIMEOUT).until(EC.element_to_be_clickable((find_by, element))).click()
        return
    except Exception:
        if alias:
            logger.warning(f"Could not click '{alias}'")
        else:
            logger.warning(f"Could not click '{element}'")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def click_by_id(element, alias=None):
    """Click an element by ID."""
    _click(element, find_by=By.ID, alias=alias)


def click_by_xpath(element, alias=None):
    _click(element, find_by=By.XPATH, alias=alias)


def click_by_link_text(element, alias=None):
    _click(element, find_by=By.LINK_TEXT, alias=alias)


def click_by_partial_link_text(element, alias=None):
    _click(element, find_by=By.PARTIAL_LINK_TEXT, alias=alias)


def click_by_name(element, alias=None):
    _click(element, find_by=By.NAME, alias=alias)


def click_by_tag_name(element, alias=None):
    _click(element, find_by=By.TAG_NAME, alias=alias)


__all__ = [
    "By",
    "QUIT_WHEN_DONE",
    "back",
    "browser",
    "click_by_id",
    "click_by_link_text",
    "click_by_name",
    "click_by_partial_link_text",
    "click_by_tag_name",
    "click_by_xpath",
    "element_exists",
    "forward",
    "go",
    "html",
    "page_contains_text",
    "refresh",
    "restore_session",
    "save_screenshot",
    "save_session",
    "timer",
]
