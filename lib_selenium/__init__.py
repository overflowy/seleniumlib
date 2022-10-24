from .lib_config import get_config, get_logging_options
from .lib_logging import setup_logging

CONFIG = get_config()

setup_logging(*get_logging_options(CONFIG))

__all__ = []
