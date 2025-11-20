import logging
import os
from datetime import datetime

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler(ERROR_LOG_FILE)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)

def get_logger(name):
    return logging.getLogger(name)
