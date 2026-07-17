import logging
from pathlib import Path

PROJECT_NAME = "random-reminder"
VERSION = "0.1.0"
DEBUG = True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_db_path():
    return "random_reminder.db"