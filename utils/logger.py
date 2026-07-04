"""
Logging utility for the AI Video Generator V2 pipeline.

Provides a configured logger with:
  - RotatingFileHandler  → LOGS_DIR / 'pipeline.log'  (DEBUG level)
  - StreamHandler        → console                     (INFO  level, colorama colours)

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Pipeline started")
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.paths import LOGS_DIR  # noqa: E402

# ── colorama init ────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)
    _COLORAMA_AVAILABLE = True
except ImportError:  # pragma: no cover – graceful fallback
    _COLORAMA_AVAILABLE = False


# ── colour formatter ────────────────────────────────────────────────────────
class _ColoredFormatter(logging.Formatter):
    """Custom formatter that injects ANSI colour codes via *colorama*."""

    _LEVEL_COLOURS: dict[int, str] = {}

    def __init__(self, fmt: str | None = None, datefmt: str | None = None) -> None:
        super().__init__(fmt, datefmt)
        if _COLORAMA_AVAILABLE:
            self._LEVEL_COLOURS = {
                logging.DEBUG: Fore.CYAN,
                logging.INFO: Fore.GREEN,
                logging.WARNING: Fore.YELLOW,
                logging.ERROR: Fore.RED,
                logging.CRITICAL: Fore.RED + Style.BRIGHT,
            }

    def format(self, record: logging.LogRecord) -> str:
        colour = self._LEVEL_COLOURS.get(record.levelno, "")
        reset = Style.RESET_ALL if colour and _COLORAMA_AVAILABLE else ""
        original = super().format(record)
        return f"{colour}{original}{reset}"


# ── constants ────────────────────────────────────────────────────────────────
_LOG_FILE = LOGS_DIR / "pipeline.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

_FILE_FMT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_CONSOLE_FMT = "%(asctime)s | %(levelname)-8s | %(message)s"

# Sentinel attribute used to detect whether our handlers are already attached.
_HANDLER_TAG = "_aivideo_handler"


# ── public API ───────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """Return a named logger pre-configured with file + console handlers.

    Calling this function multiple times with the *same* name is safe —
    handlers are added only once per logger instance.

    Args:
        name: Logical name for the logger (typically ``__name__``).

    Returns:
        A :class:`logging.Logger` ready to use.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls.
    if any(getattr(h, _HANDLER_TAG, False) for h in logger.handlers):
        return logger

    logger.setLevel(logging.DEBUG)  # let handlers decide their own level

    # ── ensure log directory exists ──────────────────────────────────────
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # ── file handler (DEBUG) ─────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FMT))
    setattr(file_handler, _HANDLER_TAG, True)
    logger.addHandler(file_handler)

    # ── console handler (INFO, coloured) ─────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_ColoredFormatter(_CONSOLE_FMT))
    setattr(console_handler, _HANDLER_TAG, True)
    logger.addHandler(console_handler)

    return logger


# ── quick smoke test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    log = get_logger("logger_test")

    log.debug("This is a DEBUG message   (file only)")
    log.info("This is an INFO message    (green)")
    log.warning("This is a WARNING message  (yellow)")
    log.error("This is an ERROR message   (red)")
    log.critical("This is a CRITICAL message (bright red)")

    # Verify duplicate-handler guard
    log2 = get_logger("logger_test")
    assert len(log2.handlers) == 2, (
        f"Expected 2 handlers, got {len(log2.handlers)}"
    )
    log.info("Duplicate-handler guard ✓  — still only 2 handlers attached")
    log.info("Log file → %s", _LOG_FILE)
