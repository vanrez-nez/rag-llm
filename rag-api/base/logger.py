import logging

LOG_LEVEL = logging.INFO

class CustomFormatter(logging.Formatter):
  """Logging Formatter to add colors and count warning / errors"""

  grey = "\x1b[38;21m"
  dim_grey = "\x1b[38;5;240m"
  blue = "\x1b[34;21m"
  yellow = "\x1b[33;21m"
  red = "\x1b[31;21m"
  bold_red = "\x1b[31;1m"
  reset = "\x1b[0m"
  format = "%(asctime)s - %(message)s"
  format_file = "%(asctime)s - %(filename)s:%(lineno)d - %(message)s"

  FORMATS = {
    logging.DEBUG: dim_grey + format,
    logging.INFO: grey + format,
    logging.WARNING: yellow + format,
    logging.ERROR: red + format_file,
    logging.CRITICAL: bold_red + format_file
  }

  def format(self, record):
    log_fmt = self.reset + self.FORMATS.get(record.levelno) + self.reset
    formatter = logging.Formatter(log_fmt, datefmt='%y/%m/%d %H:%M:%S')
    return formatter.format(record)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(CustomFormatter())
logger.addHandler(streamHandler)


def debug(msg, *args, **kwargs) -> None:
  logger.debug(msg, *args, **kwargs)

def log(msg, *args, **kwargs) -> None:
  logger.info(msg, *args, **kwargs)


def warn(msg, *args, **kwargs) -> None:
  logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs) -> None:
  logger.error(msg, *args, **kwargs)
