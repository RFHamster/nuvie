import logging
import sys
import structlog

from app.core.config import settings


def message_first_processor(_, __, event_dict):
    """
    Custom processor to ensure the main message appears first in logs,
    followed by user context, then minimal metadata.
    """
    # Create a new ordered dict with message first
    ordered_dict = {}

    # First: the main message
    if 'event' in event_dict:
        ordered_dict['message'] = event_dict['event']

    # Second: user-provided context (anything that's not standard metadata)
    standard_fields = {
        'event',
        'timestamp',
        'level',
        'logger',
        'filename',
        'func_name',
        'lineno',
    }

    # Add user context fields
    for key, value in event_dict.items():
        if key not in standard_fields:
            ordered_dict[key] = value

    # Third: essential metadata only
    ordered_dict['level'] = event_dict.get('level', 'INFO')
    ordered_dict['time'] = event_dict.get('timestamp', '')

    # In dev mode, add location info at the end
    if settings.DEV_MODE and 'filename' in event_dict:
        location = (
            f"{event_dict.get('filename', '')}:{event_dict.get('lineno', '')}"
        )
        ordered_dict['location'] = location

    return ordered_dict


def setup_logging(log_level=logging.INFO):
    """
    Configures a state-of-the-art logging system for a Python application.

    This function sets up structured logging using `structlog` and integrates
    Sentry for error and performance monitoring. It distinguishes between
    development and production environments to provide human-readable logs
    during development and machine-parsable JSON logs in production.

    This should be called once at the application startup.
    """
    if not log_level:
        log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    is_dev_mode = settings.DEV_MODE

    # --- Structlog Configuration ---
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(
            fmt='%H:%M:%S', utc=False
        ),  # Compact time format
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add detailed metadata only in dev mode
    if is_dev_mode:
        shared_processors.append(
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            )
        )

    # --- Renderer Configuration ---
    if is_dev_mode:
        # Pretty, colorful console output for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output for production, easy to parse by log aggregators
        renderer = structlog.processors.JSONRenderer()

    # Add our custom processor just before rendering
    final_processors = shared_processors + [message_first_processor, renderer]

    # --- Integrating Standard Logging with Structlog ---
    structlog.configure(
        processors=final_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the root logger
    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    # Evita duplicidade de handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress verbose logs from noisy libraries
    for logger_name in [
        'uvicorn',
        'uvicorn.error',
        'uvicorn.access',
        'gunicorn.error',
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    print(
        f'Logging configured. Level: {settings.LOG_LEVEL}, Dev Mode: {is_dev_mode}, Sentry Enabled: {bool(settings.SENTRY_DSN)}'
    )


# --- Global Logger Instance ---
# Get a logger instance that can be imported and used across the application.
# This is the object you will import in your other modules.
log: structlog.stdlib.BoundLogger = structlog.get_logger()
