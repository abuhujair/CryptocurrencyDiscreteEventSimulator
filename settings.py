import os
import logging
from datetime import datetime


BASE = os.path.dirname(os.path.abspath(__file__))

REPORT_DIR = os.path.join(BASE, f"reports_{datetime.now().strftime('%Y%m%d%H%M%S')}")

LOGGING_LEVEL = logging.DEBUG
LOG_FILE_PATHS = {
    "DEFAULT": os.path.join(REPORT_DIR, "default.log"), 
    "EVENT": os.path.join(REPORT_DIR, "event.log")
}

## CREATE DIRECTORIES
list_of_directories = [REPORT_DIR]
for directory in list_of_directories:
    if not os.path.exists(directory):
        os.makedirs(directory)