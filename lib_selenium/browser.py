import logging

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .lib_config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)

TIMEOUT = CONFIG["Browser"].get("global_timeout", 5)
DEBUG_ON_EXCEPTION = CONFIG["Browser"].get("debug_on_exception", False)


def get_browser():
    """Returns a browser instance based on the config file."""
    options = parse_browser_options(webdriver.ChromeOptions(), CONFIG["Browser"])
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)


def parse_browser_options(chrome_options, browser_config):
    """Parse browser options from config file."""

    chrome_options.binary_location = browser_config.get("chromium_executable_path")
    prefs = {
        "safebrowsing.enabled": "false",
        "profile.exit_type": "Normal",
    }
    for option in browser_config:
        match option:
            case "headless" if browser_config.get("headless"):
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--headless")
            case "sandbox" if not browser_config.get("sandbox"):
                chrome_options.add_argument("--no-sandbox")
            case "start_maximized" if browser_config.get("start_maximized"):
                chrome_options.add_argument("--start-maximized")
            case "user_agent" if user_agent := browser_config.get("user_agent"):
                chrome_options.add_argument(f"user-agent={user_agent}")
            case "chromium_profile_path" if chromium_profile_path := browser_config.get("chromium_profile_path"):
                chrome_options.add_argument(f"user-data-dir={chromium_profile_path}")
            case "disable_selenium_logging" if browser_config.get(option):
                chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            case "downloads_path" if downloads_path := browser_config.get("downloads_path"):
                prefs["download.default_directory"] = downloads_path
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options
