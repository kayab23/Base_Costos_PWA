import logging
from logging.handlers import RotatingFileHandler
import os
from .config import settings

def setup_logger():
    log_dir = os.path.dirname(settings.log_file)
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("cost_app")
    logger.setLevel(settings.log_level)
    if not logger.handlers:
        file_handler = RotatingFileHandler(
            settings.log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

logger = setup_logger()
