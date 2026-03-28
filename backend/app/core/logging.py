"""Logging configuration helpers."""

from logging.config import dictConfig


def configure_logging(level: str) -> None:
    """Configure application and server logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                }
            },
            "root": {"level": level.upper(), "handlers": ["default"]},
            "loggers": {
                "uvicorn": {"level": level.upper()},
                "uvicorn.error": {"level": level.upper(), "propagate": True},
                "uvicorn.access": {"level": level.upper(), "propagate": True},
            },
        }
    )

