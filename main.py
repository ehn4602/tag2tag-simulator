import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path


def main():
    # TODO get the log settings through CLI input
    logger, q_listener = init_logger(logging.INFO, stdout=True)

    # This is important since it ensures that all of the log has been output
    q_listener.stop()


def init_logger(level, filename="tagsim.log", stdout=False):
    """
    Initializes a logger that can then be used throughout the program.

    Arguments:
    level -- The logging level to log at
    filename -- Name of the file where the log is to be stored, tagsim.log in
                PWD by default.
    stdout -- Whether or not to print Log to stdout. False by default.

    Returns: The handle to the logger
    """
    log_queue = queue.Queue()
    qh = QueueHandler(log_queue)

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        handlers=[qh],
        format=f"%(asctime)s::%(levelname)s::{Path(__file__).name}: %(msg)s",
        level=level,
    )

    block_handlers = []

    fhandle = logging.FileHandler(filename)
    block_handlers.append(fhandle)

    if stdout:
        shandle = logging.StreamHandler()
        block_handlers.append(shandle)

    ql = QueueListener(log_queue, *block_handlers)
    ql.start()
    return logger, ql


if __name__ == "__main__":
    main()
