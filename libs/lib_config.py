import sys
from pathlib import Path

import yaml

VARS_TO_REPLACE = {
    "{{SCRIPT_DIR}}": Path(sys.argv[0]).parent.parent,
}


def replace_config_vars(config):
    for section in config.keys():
        for key, value in config[section].items():
            for var, replacement in VARS_TO_REPLACE.items():
                if not isinstance(value, str) or var not in value:
                    continue
                if isinstance(replacement, Path):
                    value = value.replace(var, str(replacement))
                    config[section][key] = str(Path(value).resolve())
                else:
                    config[section][key] = value.replace(var, replacement)
    return config


def get_config():
    with open("config.yml") as f:
        config = yaml.safe_load(f)
    return replace_config_vars(config)


def get_logging_options(config):
    path = config["Logging"]["path"]
    level = config["Logging"]["level"]
    log_exceptions = config["Logging"]["log_exceptions"]
    display_stdout = config["Logging"]["display_stdout"]
    mode = config["Logging"]["mode"]
    return path, level, log_exceptions, display_stdout, mode
