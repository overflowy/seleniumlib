import logging

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .lib_config import get_config

CONFIG = get_config()
BROWSER_CONFIG = CONFIG["browser"]
logger = logging.getLogger(__name__)
