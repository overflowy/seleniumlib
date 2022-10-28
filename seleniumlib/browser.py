import os

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from .config import get_config

CONFIG = get_config()


def get_browser(browser_config):
    """Returns a browser instance based on the config file."""
    options = parse_browser_options(webdriver.ChromeOptions(), browser_config)
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
            case "downloads_path" if downloads_path := browser_config.get("downloads_path"):
                prefs["download.default_directory"] = downloads_path
            case "disable_selenium_logging" if browser_config.get("disable_selenium_logging"):
                chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            case "disable_wdm_logging" if browser_config.get("disable_wdm_logging"):
                os.environ["WDM_LOG"] = "0"

    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options
