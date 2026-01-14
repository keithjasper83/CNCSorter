"""Structured logging configuration for CNCSorter.

This module provides centralized logging configuration, including:
- Console logging with color coding
- File logging with rotation
- JSON formatting for machine consumption (optional)
- Standardized log levels and formats
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime

# Default log format
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(
    log_dir: str = "logs",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    app_name: str = "cncsorter"
) -> None:
    """
    Configure the logging system.

    Args:
        log_dir: Directory to store log files.
        console_level: Logging level for console output.
        file_level: Logging level for file output.
        app_name: Name of the application logger.
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything at root, handlers filter

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers = []

    # Create formatters
    standard_formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)

    # 2. File Handler (Rotating)
    # Log filename includes date
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{app_name}_{current_date}.log")

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(standard_formatter)
    root_logger.addHandler(file_handler)

    # Log startup
    logging.info("=" * 60)
    logging.info(f"Logging initialized. Log file: {log_file}")
    logging.info("=" * 60)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (usually __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
