import os

os.environ["SELENIUMLIB_CFG"] = "config.json"

from seleniumlib import *

go("https://www.google.com")


if QUIT_WHEN_DONE:
    browser.quit()
