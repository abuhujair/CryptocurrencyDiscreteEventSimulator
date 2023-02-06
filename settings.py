import os
import logging

BASE = os.path.dirname(os.path.abspath(__file__))

LOGS_DIR = os.path.join(BASE, "logs")
RESULTS_DIR = os.path.join(BASE, "results")
LOGGING_LEVEL = logging.DEBUG
LOG_FILE_PATHS = {
    "DEFAULT": os.path.join(LOGS_DIR, "default.log"), 
    "EVENT": os.path.join(LOGS_DIR, "event.log")
}

## CREATE DIRECTORIES
list_of_directories = [LOGS_DIR, RESULTS_DIR]
for directory in list_of_directories:
    if not os.path.exists(directory):
        os.makedirs(directory)