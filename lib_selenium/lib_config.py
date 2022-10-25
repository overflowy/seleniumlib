import os
import re
import sys
from pathlib import Path

import yaml

EXPR = re.compile(r"{{(.*?)}}")
os.environ["SCRIPT_DIR"] = str(Path(sys.argv[0]).parent)


def extract_text_between_double_curly_braces(text):
    """Extract text between double curly braces."""
    try:
        return re.findall(EXPR, text)[0]
    except IndexError:
        return None


def normalize_path(path, as_str=True):
    """Normalize path."""
    n_path = Path(path).expanduser().resolve()
    return str(n_path) if as_str else n_path


def swap_env_vars(config):
    """Swap environment variables with their values in config."""
    for section in config.keys():
        for key, value in config[section].items():
            if not isinstance(value, str):
                continue
            if env_var := extract_text_between_double_curly_braces(value):
                config[section][key] = value.replace("{{" + env_var + "}}", os.environ[env_var])
                if "path" in key:
                    config[section][key] = normalize_path(config[section][key])
    return config


def get_config():
    """Return config after swapping environment variables."""
    with open("config.yml") as f:
        config = yaml.safe_load(f)
    return swap_env_vars(config)


def get_logging_options(config):
    """Return logging options from config."""
    path = config["Logging"].get("path")
    level = config["Logging"].get("level", "info")
    log_exceptions = config["Logging"].get("log_exceptions", True)
    display_stdout = config["Logging"].get("display_stdout", True)
    mode = config["Logging"].get("mode", "a")
    return path, level, log_exceptions, display_stdout, mode
