import sys
import logging
from logging.handlers import RotatingFileHandler
import config


def setup_logger(name: str = "subspace") -> logging.Logger:
    """
    Configures and returns a logger with both console and rotating file handlers.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(config.LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        import os
        log_dir = os.path.dirname(config.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to initialize file logging: {e}")
        
    return logger


# Shared default logger instance
logger = setup_logger()
