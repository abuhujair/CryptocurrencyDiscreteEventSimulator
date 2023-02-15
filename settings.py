import os
import logging
from datetime import datetime


BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE, "results")
REPORT_DIR = os.path.join(RESULTS_DIR, f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}")
LOGS_DIR = os.path.join(REPORT_DIR, "logs")
NODES_DIR = os.path.join(REPORT_DIR, "nodes")

LOGGING_LEVEL = logging.DEBUG
LOG_FILE_PATHS = {
    "DEFAULT": os.path.join(LOGS_DIR, "default.log"), 
    "EVENT": os.path.join(LOGS_DIR, "event.log")
}

## CREATE DIRECTORIES
list_of_directories = [LOGS_DIR, RESULTS_DIR, REPORT_DIR, NODES_DIR]
for directory in list_of_directories:
    if not os.path.exists(directory):
        os.makedirs(directory)