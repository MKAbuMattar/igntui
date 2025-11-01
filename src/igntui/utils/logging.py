#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import logging
import logging.handlers
import os
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.config import config


@dataclass
class PerformanceMetric:
    operation: str
    duration: float
    timestamp: float
    success: bool
    details: Optional[Dict[str, Any]] = None


class PerformanceLogger:
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.logger = logging.getLogger(f"{__name__}.performance")

    def record_metric(self, metric: PerformanceMetric) -> None:
        operation = metric.operation
        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(metric)

        level = logging.DEBUG if metric.success else logging.WARNING
        self.logger.log(
            level,
            f"Operation '{operation}' took {metric.duration:.3f}s (success: {metric.success})",
        )

    @contextmanager
    def measure_operation(
        self, operation_name: str, details: Optional[Dict[str, Any]] = None
    ):
        start_time = time.time()
        success = True

        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            metric = PerformanceMetric(
                operation=operation_name,
                duration=duration,
                timestamp=start_time,
                success=success,
                details=details,
            )
            self.record_metric(metric)

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        if operation:
            metrics = self.metrics.get(operation, [])
            operations = {operation: metrics}
        else:
            operations = self.metrics

        stats = {}

        for op_name, op_metrics in operations.items():
            if not op_metrics:
                continue

            durations = [m.duration for m in op_metrics]
            success_count = sum(1 for m in op_metrics if m.success)

            stats[op_name] = {
                "count": len(op_metrics),
                "success_rate": success_count / len(op_metrics),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_duration": sum(durations),
            }

        return stats

    def clear_metrics(self, operation: Optional[str] = None) -> None:
        if operation:
            self.metrics.pop(operation, None)
        else:
            self.metrics.clear()


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data, separators=(",", ":"))


class LoggingManager:
    def __init__(self):
        self.initialized = False
        self.performance_logger = PerformanceLogger()
        self._log_dir: Optional[Path] = None

    def setup_logging(
        self,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_json: bool = False,
    ) -> None:
        if self.initialized:
            return

        log_level = log_level or config.get("logging", "level")
        log_file = log_file or config.get("logging", "file")
        max_bytes = config.get("logging", "max_bytes")
        backup_count = config.get("logging", "backup_count")

        if log_file:
            self._log_dir = Path(log_file).parent
            self._log_dir.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.handlers.clear()

        if enable_json:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            root_logger.addHandler(console_handler)

        if log_file:
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(logging.DEBUG)
                root_logger.addHandler(file_handler)
            except (OSError, ValueError) as e:
                logging.warning(f"Failed to setup file logging: {e}")

        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")

        self.initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def log_config_info(self) -> None:
        """Log current configuration information."""
        logger = self.get_logger(__name__)

        config_info = {
            "log_level": logging.getLevelName(logging.getLogger().level),
            "log_dir": str(self._log_dir) if self._log_dir else None,
            "handlers": [type(h).__name__ for h in logging.getLogger().handlers],
            "performance_tracking": True,
        }

        logger.info(f"Logging configuration: {config_info}")

    def get_log_stats(self) -> Dict[str, Any]:
        root_logger = logging.getLogger()

        stats = {
            "log_level": logging.getLevelName(root_logger.level),
            "handlers": [type(h).__name__ for h in root_logger.handlers],
            "log_dir": str(self._log_dir) if self._log_dir else None,
            "performance_metrics": self.performance_logger.get_stats(),
        }

        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                try:
                    stats["log_file_size"] = os.path.getsize(handler.baseFilename)
                    stats["log_file_path"] = handler.baseFilename
                except OSError:
                    pass

        return stats

    def rotate_logs(self) -> bool:
        rotated = False

        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                try:
                    handler.doRollover()
                    rotated = True
                except Exception as e:
                    logging.warning(f"Failed to rotate log file: {e}")

        return rotated

    @contextmanager
    def measure_performance(self, operation_name: str, **kwargs):
        with self.performance_logger.measure_operation(operation_name, kwargs):
            yield

    def get_performance_stats(self) -> Dict[str, Any]:
        return self.performance_logger.get_stats()

    def clear_performance_metrics(self) -> None:
        """Clear all performance metrics."""
        self.performance_logger.clear_metrics()


logging_manager = LoggingManager()


def setup_logging(**kwargs) -> None:
    logging_manager.setup_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    return logging_manager.get_logger(name)


def measure_performance(operation_name: str, **kwargs):
    return logging_manager.measure_performance(operation_name, **kwargs)


def get_performance_stats() -> Dict[str, Any]:
    return logging_manager.get_performance_stats()
