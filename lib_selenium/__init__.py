import functools
import logging
import os
import pickle
import sys
import time
from pathlib import Path

from selenium.common.exceptions import *
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
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


def current_url():
    """Return the current URL."""
    return browser.current_url


def title():
    """Return the title of the current page."""
    return browser.title


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


def is_element_present(element, find_by=By.ID):
    """Check if element exists."""
    try:
        WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((find_by, element)))
    except NoSuchElementException:
        return False
    return True


def get_element_text(element, find_by=By.ID):
    """Get the text of an element."""
    try:
        return WebDriverWait(browser, TIMEOUT).until(EC.presence_of_element_located((find_by, element))).text
    except NoSuchElementException:
        logger.error(f"Element '{element}' not found")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def html():
    """Return the HTML of the current page."""
    return browser.page_source


def page_contains_text(text):
    """Check if page contains text."""
    return text in html()


def script(script):
    """Execute a script."""
    browser.execute_script(script)


def accept_alert():
    """Accept an alert."""
    text = None
    try:
        alert = WebDriverWait(browser, TIMEOUT).until(EC.alert_is_present())
        text = alert.text
        alert.accept()
        logger.info(f"Alert accepted: '{text}'")
    except Exception:
        if text:
            logger.error(f"Could not accept alert: '{text}'")
        logger.error("Could not accept alert")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def dismiss_alert():
    """Dismiss an alert."""
    text = None
    try:
        alert = WebDriverWait(browser, TIMEOUT).until(EC.alert_is_present())
        text = alert.text
        alert.dismiss()
        logger.info(f"Alert dismissed: '{text}'")
    except Exception:
        if text:
            logger.error(f"Could not dismiss alert: '{text}'")
        logger.error("Could not dismiss alert")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def _click(element, find_by=By.ID, alias=None):
    """Wait for an element to be available and click it."""
    try:
        WebDriverWait(browser, TIMEOUT).until(EC.element_to_be_clickable((find_by, element))).click()
        if alias:
            logger.info(f"Clicked by {find_by}: '{alias}'")
        else:
            logger.info(f"Clicked by {find_by}: '{element}'")
        return
    except Exception:
        if alias:
            logger.error(f"Could not click by {find_by}: '{alias}'")
        else:
            logger.error(f"Could not click by {find_by}: '{element}'")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def click_by_id(element, alias=None):
    """Click an element by ID."""
    _click(element, find_by=By.ID, alias=alias)


def click_by_xpath(element, alias=None):
    """Click an element by XPath."""
    _click(element, find_by=By.XPATH, alias=alias)


def click_by_link_text(element, alias=None):
    """Click an element by link text."""
    _click(element, find_by=By.LINK_TEXT, alias=alias)


def click_by_partial_link_text(element, alias=None):
    """Click an element by partial link text."""
    _click(element, find_by=By.PARTIAL_LINK_TEXT, alias=alias)


def click_by_name(element, alias=None):
    """Click an element by name."""
    _click(element, find_by=By.NAME, alias=alias)


def click_by_tag_name(element, alias=None):
    """Click an element by tag name."""
    _click(element, find_by=By.TAG_NAME, alias=alias)


def click_by_class_name(element, alias=None):
    """Click an element by class name."""
    _click(element, find_by=By.CLASS_NAME, alias=alias)


def click_by_css_selector(element, alias=None):
    """Click an element by CSS selector."""
    _click(element, find_by=By.CSS_SELECTOR, alias=alias)


def click_by_attribute(attribute, value, alias=None):
    """Click an element by an attribute value."""
    _click(f"//*[@{attribute}='{value}']", find_by=By.XPATH, alias=alias)


def _double_click(element, find_by=By.ID, alias=None):
    """Wait for an element to be available and click it."""
    try:
        el = WebDriverWait(browser, TIMEOUT).until(EC.element_to_be_clickable((find_by, element)))
        ActionChains(browser).double_click(el).perform()
        if alias:
            logger.info(f"Double clicked by {find_by}: '{alias}'")
        else:
            logger.info(f"Double clicked by {find_by}: '{element}'")
        return
    except Exception:
        if alias:
            logger.error(f"Could not double click by {find_by}: '{alias}'")
        else:
            logger.error(f"Could not double click by {find_by}: '{element}'")
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def double_click_by_id(element, alias=None):
    """Double click an element by ID."""
    _double_click(element, find_by=By.ID, alias=alias)


def double_click_by_xpath(element, alias=None):
    """Double click an element by XPath."""
    _double_click(element, find_by=By.XPATH, alias=alias)


def double_click_by_link_text(element, alias=None):
    """Double click an element by link text."""
    _double_click(element, find_by=By.LINK_TEXT, alias=alias)


def double_click_by_partial_link_text(element, alias=None):
    """Double click an element by partial link text."""
    _double_click(element, find_by=By.PARTIAL_LINK_TEXT, alias=alias)


def double_click_by_name(element, alias=None):
    """Double click an element by name."""
    _double_click(element, find_by=By.NAME, alias=alias)


def double_click_by_tag_name(element, alias=None):
    """Double click an element by tag name."""
    _double_click(element, find_by=By.TAG_NAME, alias=alias)


def double_click_by_class_name(element, alias=None):
    """Double click an element by class name."""
    _double_click(element, find_by=By.CLASS_NAME, alias=alias)


def double_click_by_css_selector(element, alias=None):
    """Double click an element by CSS selector."""
    _double_click(element, find_by=By.CSS_SELECTOR, alias=alias)


def double_click_by_attribute(attribute, value, alias=None):
    """Double click an element by an attribute value."""
    _double_click(f"//*[@{attribute}='{value}']", find_by=By.XPATH, alias=alias)


__all__ = [
    "By",
    "QUIT_WHEN_DONE",
    "accept_alert",
    "back",
    "browser",
    "click_by_attribute",
    "click_by_class_name",
    "click_by_css_selector",
    "click_by_id",
    "click_by_link_text",
    "click_by_name",
    "click_by_partial_link_text",
    "click_by_tag_name",
    "click_by_xpath",
    "current_url",
    "dismiss_alert",
    "double_click_by_attribute",
    "double_click_by_class_name",
    "double_click_by_css_selector",
    "double_click_by_id",
    "double_click_by_link_text",
    "double_click_by_name",
    "double_click_by_partial_link_text",
    "double_click_by_tag_name",
    "double_click_by_xpath",
    "forward",
    "get_element_text",
    "go",
    "html",
    "is_element_present",
    "page_contains_text",
    "refresh",
    "restore_session",
    "save_screenshot",
    "save_session",
    "script",
    "timer",
    "title",
]
