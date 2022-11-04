import os

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager


def get_browser(browser_config):
    """Returns a browser instance based on the config file."""

    chrome_options = parse_browser_options(webdriver.ChromeOptions(), browser_config)
    if page_load_strategy := browser_config.get("page_load_strategy", "normal"):
        if page_load_strategy.lower() not in ["normal", "eager", "none"]:
            raise ValueError("Invalid page load strategy. Must be one of: NORMAL, EAGER, NONE.")
        desired_caps = DesiredCapabilities.CHROME
        desired_caps["pageLoadStrategy"] = page_load_strategy.lower()
        return webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options, desired_capabilities=desired_caps
        )
    return webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


def parse_browser_options(chrome_options, browser_config):
    """Parse browser options from config file."""

    if not (chrome_executable_path := browser_config.get("chromium_executable_path")):
        raise ValueError("chrome_executable_path must be set in config file.")
    chrome_options.binary_location = chrome_executable_path

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
            case "window_size" if (
                window_size := browser_config.get("window_size") and not browser_config.get("start_maximized")
            ):
                width, height = window_size.get("width"), window_size.get("height")
                chrome_options.add_argument(f"--window-size={width},{height}")
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
