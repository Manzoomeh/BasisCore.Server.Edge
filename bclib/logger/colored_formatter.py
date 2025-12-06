import logging
import os
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'  # Gray for timestamp

    def __init__(self, fmt: str, use_colors: bool = True):
        """
        Initialize colored formatter

        Args:
            fmt: Log message format
            use_colors: Whether to use colors (default: True)
        """
        super().__init__(fmt)
        self.use_colors = use_colors and self._supports_color()

    @staticmethod
    def _supports_color() -> bool:
        """Check if the terminal supports colors"""
        # Check if stdout is a TTY and not redirected
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        # Windows 10+ supports ANSI colors
        if sys.platform == 'win32':
            try:
                import os

                # Enable ANSI escape sequences on Windows
                os.system('')
                return True
            except:
                return False
        return True

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        if self.use_colors:
            # Save original values
            levelname = record.levelname
            asctime = self.formatTime(record, self.datefmt)

            # Add color to level name
            if levelname in self.COLORS:
                record.levelname = f"{self.BOLD}{self.COLORS[levelname]}{levelname}{self.RESET}"

            # Format the message
            result = super().format(record)

            # Add gray color to timestamp (if timestamp is in the format)
            if '%(asctime)s' in self._fmt or '%(asctime)' in self._style._fmt:
                # Replace timestamp with gray colored version
                result = result.replace(
                    asctime, f"{self.GRAY}{asctime}{self.RESET}", 1)

            # Reset levelname for next use
            record.levelname = levelname
            return result
        else:
            return super().format(record)
