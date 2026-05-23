# app/config/logging.py
import sys

from loguru import logger

from app.config.settings import settings


def configure_logging():
    """Configure Loguru for console logging"""
    # Remove default handler
    logger.remove()

    # Determine log level based on environment
    log_level = "DEBUG" if settings.debug else "INFO"

    # Console logging with nice formatting
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Log startup message
    logger.info(f"Logging configured - Level: {log_level}")

    return logger


# Create the configured logger instance
log = configure_logging()
