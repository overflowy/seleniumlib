import functools
import logging
import os
import pickle
import sys
import time
from pathlib import Path

from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import get_browser
from .config import get_config
from .logger import get_logging_options, setup_logging

CONFIG = get_config()
DEBUG_ON_EXCEPTION = CONFIG["Browser"].get("debug_on_exception", False)
SCREENSHOT_ON_EXCEPTION = CONFIG["Browser"].get("screenshot_on_exception", False)
QUIT_WHEN_DONE = CONFIG["Browser"].get("quit_when_done", True)
GLOBAL_TIMEOUT_SEC = CONFIG["Browser"].get("global_timeout_sec", 5)
SESSION_PATH = CONFIG["Browser"].get("session_path")
KILL_CHROMIUM_BEFORE_START = CONFIG["Browser"].get("kill_chromium_before_start", False)
KILL_WD_BEFORE_START = CONFIG["Browser"].get("kill_wd_before_start", False)

setup_logging(*get_logging_options(CONFIG["Logging"]))
logger = logging.getLogger(__name__)


def log_action(message=None):
    """Decorator to log an action."""

    def timer(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            tic = time.perf_counter()
            value = func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            if message:
                logger.info(f"{func.__name__}::{message}::{elapsed_time:0.5f} seconds")
            else:
                logger.info(f"{func.__name__}::{elapsed_time:0.5f} seconds")
            return value

        return wrapped

    return timer


@log_action()
def kill_orphaned_processes():
    """Kill orphaned chromedriver processes if any.
    This is a workaround for killing orphaned processes
    that are not killed when the browser is manually closed."""

    if sys.platform == "win32":
        os.system("taskkill /im chromedriver.exe /f")
    else:
        os.system("pkill -f chromedriver")


@log_action()
def kill_chromium():
    """Kill chromium processes."""

    if sys.platform == "win32":
        os.system("taskkill /im chrome.exe /f")
    else:
        os.system("pkill -f chrome")


if not QUIT_WHEN_DONE or KILL_WD_BEFORE_START:
    kill_orphaned_processes()

if KILL_CHROMIUM_BEFORE_START:
    kill_chromium()

browser = get_browser(CONFIG["Browser"])


def current_url():
    """Return the current URL."""

    return browser.current_url


def title():
    """Return the title of the current page."""

    return browser.title


def go(url):
    """Go to a URL."""

    @log_action(f"Go to {url}")
    def _go():
        browser.get(url)

    _go()


@log_action()
def refresh():
    """Refresh the current page."""

    browser.refresh()


@log_action()
def back():
    """Go back to the previous page."""

    browser.back()


@log_action()
def forward():
    """Go forward to the next page."""

    browser.forward()


def wait(sec):
    """Wait for a number of seconds."""

    @log_action(f"Wait for {sec} seconds")
    def _wait():
        browser.implicitly_wait(sec)

    _wait()


def get_cookies():
    """Return the cookies."""

    return browser.get_cookies()


def add_cookie(cookie):
    """Add a cookie: {name: value}."""

    @log_action(f"Add cookie {cookie}")
    def _add_cookie(cookie):
        browser.add_cookie(cookie)

    _add_cookie(cookie)


def check_session_path():
    """Check if session path is set."""

    if not SESSION_PATH:
        raise ValueError("Session path is not set")


@log_action()
def save_session():
    """Save the current session to a file."""

    check_session_path()

    cookies = get_cookies()
    cookies.insert(0, {"url": browser.current_url})

    with open(SESSION_PATH, "wb") as f:
        try:
            pickle.dump(cookies, f)
            logger.info(f"Session saved to {SESSION_PATH}>")
        except FileNotFoundError:
            logger.error("Error saving session.")


@log_action()
def restore_session():
    """Restore the session from a file."""

    check_session_path()

    with open(SESSION_PATH, "rb") as f:
        try:
            cookies = pickle.load(f)
            go(cookies.pop(0)["url"])
            for cookie in cookies:
                add_cookie(cookie)
            refresh()  # Refresh to apply cookies.
            logger.info(f"Session restored from {SESSION_PATH}")
        except Exception:
            logger.error("Error restoring session.")


@log_action()
def save_screenshot(name=None):
    """Save a screenshot of the current page."""

    if not (screenshots_path := CONFIG["Browser"].get("screenshots_path")):
        raise ValueError("Screenshots path not set in config.")

    if not Path(screenshots_path).exists():
        Path(screenshots_path).mkdir(parents=True)
    if name:
        filename = str(Path(screenshots_path) / Path(f"screenshot_{name}_{time.time()}.png"))
    else:
        filename = str(Path(screenshots_path) / Path(f"screenshot_{time.time()}.png"))
    browser.save_screenshot(filename)
    logger.info(f"Screenshot saved to {filename}")


def html():
    """Return the HTML of the current page."""

    return browser.page_source


def source():
    """Alias function for `html`."""

    return html()


def page_contains_text(text):
    """Check if page contains text."""

    return text in html()


def script(script):
    """Execute a script."""

    @log_action(f"Execute script {script}")
    def _script():
        browser.execute_script(script)

    _script()


def get_alert():
    """Get an alert object."""

    try:
        return WebDriverWait(browser, GLOBAL_TIMEOUT_SEC).until(EC.alert_is_present())
    except Exception:  # TODO: Be more specific.
        logger.error("Alert not found")
        if SCREENSHOT_ON_EXCEPTION:
            save_screenshot()
        if DEBUG_ON_EXCEPTION:
            breakpoint()


@log_action()
def accept_alert():
    """Accept an alert."""

    alert_text = None
    alert = get_alert()
    alert_text = alert.text
    alert.accept()
    logger.info(f"Alert accepted: {alert_text}")


@log_action()
def dismiss_alert():
    """Dismiss an alert."""

    alert_text = None
    alert = get_alert()
    alert_text = alert.text
    alert.dismiss()
    logger.info(f"Alert dismissed: {alert_text}")


def get_element_obj(element, find_by=By.ID):
    """Get an element from the page."""

    try:
        return WebDriverWait(browser, GLOBAL_TIMEOUT_SEC).until(EC.presence_of_element_located((find_by, element)))
    except NoSuchElementException:
        logger.error(f"Element {element} not found (method: {find_by})")
        if SCREENSHOT_ON_EXCEPTION:
            save_screenshot()
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def get_element_text(element, find_by=By.ID):
    """Get the text of an element."""

    return get_element_obj(element, find_by).text


def get_element_by_attr_value(attribute, value):
    """Get an element by attribute value."""

    return get_element_obj(f"//*[@{attribute}='{value}']", find_by=By.XPATH)


@log_action()
def click(element, find_by=By.LINK_TEXT, alias=None):
    """Wait for an element to be available and click it."""

    @log_action(f"Click {alias or element} (method: {find_by})")
    def _click(element, find_by):
        get_element_obj(element, find_by).click()

    _click(element, find_by)


def click_by_attr_value(attribute, value, alias=None):
    """Click an element by attribute value."""

    @log_action(f"Click {attribute}={value} {alias or ''}")
    def _click_by_attr_value(attribute, value):
        get_element_by_attr_value(attribute, value).click()

    _click_by_attr_value(attribute, value)


@log_action()
def double_click(element, find_by=By.LINK_TEXT, alias=None):
    """Wait for an element to be available and click it."""

    element_obj = get_element_obj(element, find_by)
    ActionChains(browser).double_click(element_obj).perform()
    if alias:
        logger.info(f"Double clicked by {find_by}: {alias}")
    else:
        logger.info(f"Double clicked by {find_by}: {element}")


def clear_text(element_obj):
    """Clear text from an element."""

    element_obj.send_keys(Keys.CONTROL + "a")
    element_obj.send_keys(Keys.DELETE)


def write(text, into=None, find_by=By.ID, alias=None, clear_first=True):
    """Wait for an element to be available and write into it.
    If no element is specified, simply write into the current page.
    """

    if not into:
        ActionChains(browser).send_keys(text).perform()
        return

    element_obj = get_element_obj(into, find_by)
    if clear_first:
        clear_text(element_obj)
    element_obj.send_keys(text)
    if alias:
        logger.info(f"Wrote into by {find_by}: '{alias}'")
    else:
        logger.info(f"Wrote into by {find_by}: '{into}'")


__all__ = [
    "By",
    "QUIT_WHEN_DONE",
    "accept_alert",
    "add_cookie",
    "back",
    "browser",
    "click",
    "click_by_attr_value",
    "current_url",
    "dismiss_alert",
    "double_click",
    "forward",
    "get_cookies",
    "get_element_obj",
    "get_element_by_attr_value",
    "get_element_text",
    "go",
    "html",
    "page_contains_text",
    "refresh",
    "restore_session",
    "save_screenshot",
    "save_session",
    "script",
    "title",
    "write",
    "wait",
]
