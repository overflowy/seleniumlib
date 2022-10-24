# Python Selenium Template 🚀

Minimal template for web scraping projects using Python and Selenium

## Installation

- Clone the repository
- Make sure you have Python 3.10 or newer installed
- Install the required packages `pip install -r requirements.txt` (recommended to use a virtual environment)
  - Or `pip install selenium webdriver-manager pyyaml`
- Download Chromium (for Windows, portable builds can be found [here](https://chromium.woolyss.com/))
- Edit `config.yaml` and set the path to the Chromium executable (`Browser.chromium_executable_path`)
- Define execution steps in `playbook.py`
- Run `python main.py`
