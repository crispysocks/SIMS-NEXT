import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

COLOR_CODES = {
    logging.DEBUG: "\033[1;36m",    # cyan
    logging.INFO: "\033[1;32m",     # green
    logging.WARNING: "\033[1;33m",  # yellow
    logging.ERROR: "\033[1;31m",     # red
    logging.CRITICAL: "\033[1;35m", # magenta
}
RESET = "\033[0m"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{COLOR_CODES.get(record.levelno, '')}{record.levelname}{RESET}"
        return super().format(record)

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    fmt = "%(asctime)s %(levelname)-8s %(message)s"
    console_fmt = "%(asctime)s %(levelname)-8s %(message)s"

    # console handler
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.addFilter(lambda r: True)  # all levels
    console.setFormatter(ColoredFormatter(console_fmt))
    root.addHandler(console)

    # normal log file - all levels, daily rotation
    normal_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    normal_handler.setLevel(logging.DEBUG)
    normal_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(normal_handler)

    # error log file - ERROR+ only, daily rotation
    error_handler = TimedRotatingFileHandler(
        LOG_DIR / "error.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(error_handler)

setup_logging()