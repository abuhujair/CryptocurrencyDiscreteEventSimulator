import logging

import settings

def get_logger(logger_name:str):
    """Fetches the logger with the given logger name

    Args:
        logger_name (str): Unique logger name

    Returns:
        logging.Logger: Generated logger with the specifications
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.LOGGING_LEVEL)
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s : %(message)s", datefmt="%d/%m/%Y %I:%M:%S %p")
    
    if logger_name in settings.LOG_FILE_PATHS.keys():
        path = f"{settings.LOG_FILE_PATHS[logger_name]}"
    else:
        path = settings.LOG_FILE_PATHS['DEFAULT']
    file_handler = logging.FileHandler(path)
    file_handler.setLevel(settings.LOGGING_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger