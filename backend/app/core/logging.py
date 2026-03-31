import logging
from pythonjsonlogger import jsonlogger


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    if root_logger.handlers:
        handler = root_logger.handlers[0]
    else:
        handler = logging.StreamHandler()
        root_logger.addHandler(handler)

    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
