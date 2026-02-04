#!/usr/bin/env python3
"""
Dharmic Logging - Structured JSON logging for DHARMIC_GODEL_CLAW.

Features:
- JSON-formatted logs for machine parsing
- Custom DHARMIC level for gate events
- Automatic rotation (10MB per file, keep 5)
- Context-rich log entries with component tracking

Usage:
    from src.core.dharmic_logging import get_logger
    
    logger = get_logger("dgm_lite")
    logger.info("Processing started", context={"cycle": 1})
    logger.dharmic("Gate passed", gate="ahimsa", result=True)
"""
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Custom log level for dharmic gate events
DHARMIC_LEVEL = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(DHARMIC_LEVEL, "DHARMIC")

# Default log directory
LOG_DIR = Path.home() / "DHARMIC_GODEL_CLAW" / "logs"
LOG_FILE = LOG_DIR / "dgc.jsonl"

# Rotation settings
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON string."""
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }
        
        # Add context if present (passed via extra)
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context
        
        # Add dharmic-specific fields for gate events
        if hasattr(record, "gate"):
            log_entry["gate"] = record.gate
        if hasattr(record, "gate_result"):
            log_entry["gate_result"] = record.gate_result
        if hasattr(record, "fitness"):
            log_entry["fitness"] = record.fitness
        if hasattr(record, "entry_id"):
            log_entry["entry_id"] = record.entry_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add source location for errors
        if record.levelno >= logging.ERROR:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        return json.dumps(log_entry, default=str)


class DharmicLogger(logging.Logger):
    """Extended Logger with dharmic() method for gate events."""
    
    def dharmic(
        self, 
        msg: str, 
        gate: str = None,
        result: bool = None,
        fitness: float = None,
        entry_id: str = None,
        context: Dict[str, Any] = None,
        **kwargs
    ):
        """Log a dharmic gate event.
        
        Args:
            msg: Log message
            gate: Name of the dharmic gate (ahimsa, satya, etc.)
            result: Whether the gate passed
            fitness: Fitness score if relevant
            entry_id: Archive entry ID if relevant
            context: Additional context dict
        """
        if self.isEnabledFor(DHARMIC_LEVEL):
            extra = {
                "context": context or {},
            }
            if gate:
                extra["gate"] = gate
            if result is not None:
                extra["gate_result"] = result
            if fitness is not None:
                extra["fitness"] = fitness
            if entry_id:
                extra["entry_id"] = entry_id
            
            self._log(DHARMIC_LEVEL, msg, args=(), extra=extra, **kwargs)
    
    def info(self, msg: str, context: Dict[str, Any] = None, *args, **kwargs):
        """Log info with optional context."""
        if context:
            kwargs.setdefault("extra", {})["context"] = context
        super().info(msg, *args, **kwargs)
    
    def debug(self, msg: str, context: Dict[str, Any] = None, *args, **kwargs):
        """Log debug with optional context."""
        if context:
            kwargs.setdefault("extra", {})["context"] = context
        super().debug(msg, *args, **kwargs)
    
    def warning(self, msg: str, context: Dict[str, Any] = None, *args, **kwargs):
        """Log warning with optional context."""
        if context:
            kwargs.setdefault("extra", {})["context"] = context
        super().warning(msg, *args, **kwargs)
    
    def error(self, msg: str, context: Dict[str, Any] = None, *args, **kwargs):
        """Log error with optional context."""
        if context:
            kwargs.setdefault("extra", {})["context"] = context
        super().error(msg, *args, **kwargs)


# Register custom logger class
logging.setLoggerClass(DharmicLogger)


def _ensure_log_dir():
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _create_file_handler() -> logging.Handler:
    """Create rotating file handler for JSON logs."""
    _ensure_log_dir()
    
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(JsonFormatter())
    handler.setLevel(logging.DEBUG)
    return handler


def _create_console_handler() -> logging.Handler:
    """Create console handler for human-readable output."""
    handler = logging.StreamHandler()
    # Human-readable format for console
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    return handler


# Singleton setup - handlers added once
_initialized = False
_root_handler: Optional[logging.Handler] = None
_console_handler: Optional[logging.Handler] = None


def setup_logging(
    level: int = logging.DEBUG,
    console: bool = True,
    file: bool = True,
) -> None:
    """Initialize the dharmic logging system.
    
    Args:
        level: Minimum log level
        console: Enable console output
        file: Enable file output
    """
    global _initialized, _root_handler, _console_handler
    
    if _initialized:
        return
    
    root = logging.getLogger()
    root.setLevel(level)
    
    if file:
        _root_handler = _create_file_handler()
        root.addHandler(_root_handler)
    
    if console:
        _console_handler = _create_console_handler()
        root.addHandler(_console_handler)
    
    _initialized = True


def get_logger(name: str) -> DharmicLogger:
    """Get a dharmic logger for the given component.
    
    Args:
        name: Logger name (usually module or component name)
        
    Returns:
        DharmicLogger instance with dharmic() method
        
    Example:
        logger = get_logger("dgm_lite")
        logger.info("Starting cycle", context={"generation": 1})
        logger.dharmic("Gate evaluated", gate="ahimsa", result=True)
    """
    # Ensure logging is set up
    setup_logging()
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Ensure it's our custom class
    if not isinstance(logger, DharmicLogger):
        # This can happen if logger was created before our class was registered
        # We wrap it with our methods
        logger.dharmic = lambda msg, **kw: logger.log(
            DHARMIC_LEVEL, msg, extra={
                "context": kw.get("context", {}),
                "gate": kw.get("gate"),
                "gate_result": kw.get("result"),
                "fitness": kw.get("fitness"),
                "entry_id": kw.get("entry_id"),
            }
        )
    
    return logger


def log_gate_event(
    logger: logging.Logger,
    gate: str,
    passed: bool,
    component: str = None,
    details: Dict[str, Any] = None,
):
    """Convenience function to log gate evaluation.
    
    Args:
        logger: Logger instance
        gate: Gate name (ahimsa, satya, etc.)
        passed: Whether the gate passed
        component: Component being evaluated
        details: Additional context
    """
    msg = f"Gate '{gate}' {'PASSED' if passed else 'FAILED'}"
    context = details or {}
    if component:
        context["component"] = component
    
    if hasattr(logger, "dharmic"):
        logger.dharmic(msg, gate=gate, result=passed, context=context)
    else:
        # Fallback for non-dharmic loggers
        level = logging.INFO if passed else logging.WARNING
        logger.log(level, msg, extra={"context": context})


def log_fitness(
    logger: logging.Logger,
    fitness: float,
    entry_id: str = None,
    component: str = None,
    breakdown: Dict[str, float] = None,
):
    """Convenience function to log fitness evaluation.
    
    Args:
        logger: Logger instance
        fitness: Total fitness score
        entry_id: Archive entry ID
        component: Component evaluated
        breakdown: Fitness component breakdown
    """
    msg = f"Fitness evaluated: {fitness:.3f}"
    context = {}
    if component:
        context["component"] = component
    if breakdown:
        context["breakdown"] = breakdown
    
    if hasattr(logger, "dharmic"):
        logger.dharmic(msg, fitness=fitness, entry_id=entry_id, context=context)
    else:
        logger.info(msg, extra={"context": context})


class ModelError(RuntimeError):
    """Error raised when model backend fails."""
    pass


# Auto-setup on import for convenience
setup_logging()
