from loguru import logger


def setup_logging() -> None:
    """
    Configure loguru for simple console logging.

    This keeps logging setup in one place and can be extended later
    (e.g., file logs, JSON logs for evaluation runs).
    """
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
        backtrace=False,
        diagnose=False,
    )


__all__ = ["logger", "setup_logging"]

