import logging

logger = logging.getLogger(__name__)


class ErrorReporter:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn

    def capture_exception(self, error: Exception) -> None:
        logger.exception("error_captured", extra={"dsn_configured": bool(self.dsn)}, exc_info=error)
