import json
import os
import re
import sys
from pathlib import Path


ENV_VAR_EXPR = re.compile(r"{{(.*?)}}")
os.environ["SCRIPT_DIR"] = str(Path(sys.argv[0]).parent)


def extract_text_between_double_curly_braces(text):
    """Extract environment variable between double curly braces."""
    try:
        return re.findall(ENV_VAR_EXPR, text)[0]
    except IndexError:
        return None


def normalize_path(path, as_str=True):
    """Normalize path."""
    n_path = Path(path).expanduser().resolve()
    return str(n_path) if as_str else n_path


def expand_env_vars(config):
    """Expand environment variables in config if they have been defined."""
    for section in config.keys():
        for key, value in config[section].items():
            if not isinstance(value, str):
                continue
            if env_var := extract_text_between_double_curly_braces(value) and os.environ.get(env_var):
                config[section][key] = value.replace("{{" + env_var + "}}", os.environ[env_var])
                if "path" in key:
                    config[section][key] = normalize_path(config[section][key])
    return config


def try_open_config_file(config_file):
    """Try to open config file."""
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_file} not found.")
        sys.exit(1)


def get_config():
    """Return config after expanding environment variables.
    If available, use path defined via SELENIUMLIB_CFG env var."""
    if seleniumlib_cfg := os.environ.get("SELENIUMLIB_CFG"):
        config = try_open_config_file(seleniumlib_cfg)
    else:
        config = try_open_config_file("config.json")
    return expand_env_vars(config)


def get_logging_options(config):
    """Return logging options from config."""
    log_path = config["Logging"].get("log_path")
    level = config["Logging"].get("level", "info")
    log_exceptions = config["Logging"].get("log_exceptions", True)
    display_stdout = config["Logging"].get("display_stdout", True)
    mode = config["Logging"].get("mode", "a")
    return log_path, level, log_exceptions, display_stdout, mode
