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
    """Kill orphaned `chromedriver` processes if any.
    This is a workaround for killing orphaned processes
    that are not killed when the browser is manually closed."""

    if sys.platform == "win32":
        os.system("taskkill /im chromedriver.exe /f")
    else:
        os.system("pkill -f chromedriver")


@log_action()
def kill_chromium():
    """Kill `chromium` processes."""

    if sys.platform == "win32":
        os.system("taskkill /im chrome.exe /f")
    else:
        os.system("pkill -f chrome")


if not QUIT_WHEN_DONE or KILL_WD_BEFORE_START:
    kill_orphaned_processes()

if KILL_CHROMIUM_BEFORE_START:
    kill_chromium()

browser = get_browser(CONFIG["Browser"])


def close():
    """Close the browser."""

    @log_action()
    def _close():
        browser.close()

    _close()


def quit():
    """Close the browser. Alias function for `close`."""
    close()


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
        time.sleep(sec)

    _wait()


def wait_until_page_contains(text, timeout=GLOBAL_TIMEOUT_SEC):
    """Wait until the page contains the given text."""

    @log_action(f"Wait until page contains {text}")
    def _wait_until_page_contains():
        try:
            WebDriverWait(browser, timeout).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))
        except TimeoutException:
            logger.critical(f"Timeout waiting for page to contain -> {text}")

    _wait_until_page_contains()


def get_cookies():
    """Return the cookies."""

    return browser.get_cookies()


def add_cookie(cookie):
    """Add a cookie: `{name: value}`."""

    @log_action(f"Add cookie {cookie}")
    def _add_cookie():
        browser.add_cookie(cookie)

    _add_cookie()


def check_session_path():
    """Check if session path is set."""

    if not SESSION_PATH:
        raise ValueError("session_path <- Value not set in config file.")


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
            logger.critical("Error saving session.")


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
            logger.critical("Error restoring session.")


def save_screenshot(name=None):
    """Save a screenshot of the current page."""

    if not (screenshots_path := CONFIG["Browser"].get("screenshots_path")):
        raise ValueError("screenshots_path <- Value not set in config file.")
    if not Path(screenshots_path).exists():
        Path(screenshots_path).mkdir(parents=True)

    if name:
        filename = str(Path(screenshots_path) / Path(f"screenshot_{name}_{time.time()}.png"))
    else:
        filename = str(Path(screenshots_path) / Path(f"screenshot_{time.time()}.png"))

    @log_action(f"Save screenshot to {filename}")
    def _save_screenshot():
        browser.save_screenshot(filename)

    _save_screenshot()


def save_screenshot_every_n_sec(n_sec, until_sec=0, name=None):
    """Save a screenshot every `n` seconds, until `until_sec` seconds have passed."""

    if not until_sec:
        while True:
            save_screenshot(name)
            time.sleep(n_sec)
    else:
        if until_sec <= n_sec:
            raise ValueError("until_sec <- Must be greater than n_sec.")

        seconds_passed = 0
        while seconds_passed < until_sec:
            wait(n_sec)
            seconds_passed += n_sec
            save_screenshot(name=name)


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
        logger.critical("Alert not found")
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
    """Get the object of an element."""

    try:
        match element:
            case str():
                return WebDriverWait(browser, GLOBAL_TIMEOUT_SEC).until(
                    EC.presence_of_element_located((find_by, element))
                )
            case (str(), str()):
                try:
                    attr, value = element
                    return WebDriverWait(browser, GLOBAL_TIMEOUT_SEC).until(
                        EC.presence_of_element_located((By.XPATH, f"//*[@{attr}='{value}']"))
                    )
                except ValueError:
                    TypeError(f"{repr(element)} <- Invalid element tuple. Must be (attr, value).")
            case _:
                raise TypeError("f{repr(element)} <- Invalid element type. Must be str or tuple[str, str].")

    except TimeoutException:
        logger.critical(f"{element} <- Element not found.")
        if SCREENSHOT_ON_EXCEPTION:
            save_screenshot()
        if DEBUG_ON_EXCEPTION:
            breakpoint()


def get_element_text(element, find_by=By.ID):
    """Get the text of an element."""

    return get_element_obj(element, find_by).text


def click(element, find_by=By.LINK_TEXT, alias=None):
    """Wait for an element to be available and click it."""

    @log_action(f"Click {alias or element} (method: {find_by})")
    def _click():
        get_element_obj(element, find_by).click()

    _click()


def double_click(element, find_by=By.LINK_TEXT, alias=None):
    """Wait for an element to be available and click it."""

    @log_action(f"Double click {alias or element} (method: {find_by})")
    def _double_click():
        element_obj = get_element_obj(element, find_by)
        ActionChains(browser).double_click(element_obj).perform()

    _double_click()


def clear_text(element_obj):
    """Clear text from an element object."""

    element_obj.send_keys(f"{Keys.CONTROL}a")
    element_obj.send_keys(Keys.DELETE)


def write(text, into_element=None, find_by=By.ID, alias=None, clear_first=True):
    """Wait for an element to be available and write into it.
    If no element is specified, send keys to the current page."""

    @log_action(f"Write {text} into {alias or into_element} (method: {find_by})")
    def _write():
        if into_element:
            element_obj = get_element_obj(into_element, find_by)
            if clear_first:
                # element_obj.clear()  # This doesn't work apparently.
                clear_text(element_obj)
            element_obj.send_keys(text)
        else:
            ActionChains(browser).send_keys(text).perform()
            return

    _write()


__all__ = [
    "By",
    "QUIT_WHEN_DONE",
    "accept_alert",
    "add_cookie",
    "back",
    "browser",
    "click",
    "close",
    "current_url",
    "dismiss_alert",
    "double_click",
    "forward",
    "get_alert",
    "get_cookies",
    "get_element_obj",
    "get_element_text",
    "go",
    "html",
    "kill_chromium",
    "kill_orphaned_processes",
    "log_action",
    "page_contains_text",
    "quit",
    "refresh",
    "restore_session",
    "save_screenshot",
    "save_screenshot_every_n_sec",
    "save_session",
    "script",
    "source",
    "title",
    "wait",
    "wait_until_page_contains",
    "write",
]
