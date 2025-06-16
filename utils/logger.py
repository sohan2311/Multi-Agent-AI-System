"""
Logging utility for the multi-agent system.
Provides consistent logging across all components.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class AgentLogger:
    """Main logger class for the multi-agent system."""
    
    def __init__(self, name: str = "multi_agent_system"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with console and file handlers."""
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set log level from environment or default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_file = log_dir / f"agent_system_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_agent_start(self, agent_name: str, task: str):
        """Log when an agent starts executing."""
        self.logger.info(f"🤖 {agent_name.upper()} AGENT STARTED | Task: {task}")
    
    def log_agent_success(self, agent_name: str, result_summary: str):
        """Log successful agent execution."""
        self.logger.info(f"✅ {agent_name.upper()} AGENT SUCCESS | {result_summary}")
    
    def log_agent_error(self, agent_name: str, error: str):
        """Log agent execution error."""
        self.logger.error(f"❌ {agent_name.upper()} AGENT ERROR | {error}")
    
    def log_api_call(self, api_name: str, endpoint: str, status: str = "SUCCESS"):
        """Log API calls."""
        if status == "SUCCESS":
            self.logger.debug(f"🌐 API CALL | {api_name} | {endpoint} | ✅")
        else:
            self.logger.warning(f"🌐 API CALL | {api_name} | {endpoint} | ❌ {status}")
    
    def log_system_start(self):
        """Log system startup."""
        self.logger.info("=" * 50)
        self.logger.info("🚀 MULTI-AGENT SYSTEM STARTED")
        self.logger.info("=" * 50)
    
    def log_system_shutdown(self):
        """Log system shutdown."""
        self.logger.info("=" * 50)
        self.logger.info("🛑 MULTI-AGENT SYSTEM SHUTDOWN")
        self.logger.info("=" * 50)
    
    def log_goal_processing(self, goal: str):
        """Log goal processing start."""
        self.logger.info(f"🎯 PROCESSING GOAL: {goal}")
    
    def log_execution_plan(self, agents: list):
        """Log the planned execution sequence."""
        agent_list = " → ".join(agents)
        self.logger.info(f"📋 EXECUTION PLAN: {agent_list}")
    
    def log_performance_metrics(self, metrics: dict):
        """Log performance metrics."""
        self.logger.info("📊 PERFORMANCE METRICS:")
        for key, value in metrics.items():
            self.logger.info(f"   {key}: {value}")


# Global logger instance
_global_logger = None


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the given name and configuration.
    This function provides backward compatibility with the original import.
    
    Args:
        name (str): Name of the logger
        log_file (str, optional): Path to log file. If None, uses default logging setup.
        level (int): Logging level (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global _global_logger
    
    # Set log level environment variable if different from INFO
    if level != logging.INFO:
        os.environ['LOG_LEVEL'] = logging.getLevelName(level)
    
    # Initialize global logger if not already done
    if _global_logger is None:
        _global_logger = AgentLogger(name)
    
    # Return a child logger with the specified name
    return _global_logger.get_logger().getChild(name) if name != _global_logger.name else _global_logger.get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the specified name."""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = AgentLogger()
    
    if name:
        # Create a child logger
        return _global_logger.get_logger().getChild(name)
    else:
        return _global_logger.get_logger()


def setup_logging(log_level: str = None):
    """Setup logging configuration."""
    global _global_logger
    
    if log_level:
        os.environ['LOG_LEVEL'] = log_level
    
    _global_logger = AgentLogger()
    return _global_logger


# Convenience functions
def log_info(message: str, agent_name: str = None):
    """Log info message."""
    logger = get_logger(agent_name)
    logger.info(message)


def log_error(message: str, agent_name: str = None):
    """Log error message."""
    logger = get_logger(agent_name)
    logger.error(message)


def log_warning(message: str, agent_name: str = None):
    """Log warning message."""
    logger = get_logger(agent_name)
    logger.warning(message)


def log_debug(message: str, agent_name: str = None):
    """Log debug message."""
    logger = get_logger(agent_name)
    logger.debug(message)


# Context manager for logging agent execution
class LogAgentExecution:
    """Context manager for logging agent execution."""
    
    def __init__(self, agent_name: str, task: str):
        self.agent_name = agent_name
        self.task = task
        self.logger = get_logger()
    
    def __enter__(self):
        self.logger.info(f"🤖 {self.agent_name.upper()} AGENT STARTED | Task: {self.task}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"✅ {self.agent_name.upper()} AGENT COMPLETED")
        else:
            self.logger.error(f"❌ {self.agent_name.upper()} AGENT FAILED | {exc_val}")
        return False


if __name__ == "__main__":
    # Test the logger
    setup_logging("DEBUG")
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test context manager
    with LogAgentExecution("test_agent", "testing functionality"):
        logger.info("Agent is working...")
    
    # Test the setup_logger function
    test_logger = setup_logger("test_setup_logger")
    test_logger.info("Testing setup_logger function")