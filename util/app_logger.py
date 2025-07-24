from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
import logging
from logging.handlers import QueueHandler, QueueListener
import os
import queue

from pythonjsonlogger.jsonlogger import JsonFormatter
from state import AppState

if TYPE_CHECKING:
    from tags.tag import Tag


# Add sympy time to logging
class TimeInjector(logging.Filter):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

    def filter(self, record):
        record.simpy_time = self.app_state.now()
        return True


def verify_log_directory(base_filename: str):
    """
    Verifies that the log directory exists, and creates it if it does not.

    Arguments:
    base_filename -- The output filename for the log, which is used to determine
                     the directory where the log will be stored.
    """
    directory = os.path.dirname(base_filename)
    if not os.path.exists(directory):
        os.makedirs(directory)


def init_logger(
    app_state: AppState,
    level,
    logger_name=None,
    base_filename="tagsim.log",
    stdout=False,
) -> tuple[logging.Logger, QueueListener]:
    """
    Initializes a logger that can be used throughout the program.

    Arguments:
        level: The logging level to log at.
        filename (str): Name of the file where the log is to be stored, tagsim.log in
        PWD/logs by default.
        stdout (bool): Whether or not to print Log to stdout. False by default.

    Returns:
        logger, queue_listener (tuple[logging.Logger, QueueListener]): Logger objects.
    """
    directory = "logs"
    base_filename = os.path.join(directory, base_filename)
    verify_log_directory(base_filename)

    # Create the logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Create formatters
    text_formatter = logging.Formatter(
        fmt=f"t=%(simpy_time)s::%(levelname)s::{logger.name}: %(msg)s",
    )
    json_formatter = JsonFormatter(
        fmt="%(simpy_time)s %(levelname)s %(message)s",
        rename_fields={
            "simpy_time": "time",
            "levelname": "level",
            "message": "msg",
        },
    )

    # Create queue for threaded l
    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.addFilter(TimeInjector(app_state))
    logger.addHandler(queue_handler)

    time_format = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")

    # Output JSON
    json_file_handler = logging.FileHandler(f"{base_filename}-{time_format}.json")
    json_file_handler.setFormatter(json_formatter)

    info_file_handler = logging.FileHandler(f"{base_filename}-{time_format}.log")
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(text_formatter)

    handlers = [json_file_handler, info_file_handler]

    if stdout:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(text_formatter)
        handlers.append(stream_handler)

    ql = QueueListener(log_queue, *handlers, respect_handler_level=True)
    ql.start()

    return logger, ql


class TagLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None, merge_extra=False):
        super().__init__(logger, extra, merge_extra)
        self.tag_name = extra["tag"]

    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)
        return f"[Tag {self.tag_name}] {msg}", kwargs


def init_tag_logger(tag: Tag) -> logging.LoggerAdapter:
    """
    Initializes a logger specifically for a tag.

    Arguments:
    tag -- The tag for which the logger is being initialized.

    Returns: The newly created logger for the tag.
    """
    tag_logger = logging.getLogger(f"tag.{tag.name}")
    added_context = {"tag": tag.name}
    return TagLoggerAdapter(tag_logger, extra=added_context, merge_extra=True)
