"""Logger DI registration."""
from bclib.logger import ILogger
from bclib.logger.console_logger import ConsoleLogger


def test_default_logger_is_console(app):
    logger = app.service_provider.get_service(ILogger["PytestApp"])
    assert isinstance(logger, ConsoleLogger)
    assert hasattr(logger, "info")
    logger.debug("unit-test log line")
