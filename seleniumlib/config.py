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
            if env_var := extract_text_between_double_curly_braces(value):
                if not os.environ.get(env_var):
                    return
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
