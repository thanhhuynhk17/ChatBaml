import logging
import logging.config


def setup_logging(default_level=logging.INFO):
    """Configure logging for the entire package."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "INFO",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": default_level,
        },
    }
    logging.config.dictConfig(logging_config)
