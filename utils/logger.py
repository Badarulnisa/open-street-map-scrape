"""
Single source of truth for logging setup. Import get_logger(__name__)
anywhere instead of calling logging.basicConfig repeatedly.
"""

import logging
from pathlib import Path

import config


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured (avoids duplicate handlers on re-import).
        return logger

    logger.setLevel(config.LOG_LEVEL)

    formatter = logging.Formatter(config.LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file: Path = config.LOG_DIR / "pipeline.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger