import json
import logging
import sys
from logging.config import dictConfig

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s"

class JSONFormatter(logging.Formatter):
    """
    JSONFormatter serializes logging statements to standardized JSON strings,
    capturing caller module, line numbers, category tags, and stack traces.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
            "category": getattr(record, "category", "general"),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO") -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
            "structured_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "app_structured.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf8",
            }
        },
        "root": {
            "handlers": ["console", "structured_file"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console", "structured_file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "level": log_level,
            },
            "uvicorn.access": {
                "handlers": ["console", "structured_file"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    dictConfig(logging_config)
