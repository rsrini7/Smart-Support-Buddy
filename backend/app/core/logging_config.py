import logging
import sys
import os

def setup_logging():
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create formatter and add it to the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(console_handler)

    # Use a relative path for the log file
    rel_log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'backend.log')
    log_dir = os.path.dirname(rel_log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(rel_log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set levels for specific loggers
    logging.getLogger('app.services.jira_service').setLevel(logging.DEBUG)
    logging.getLogger('app.services.msg_parser').setLevel(logging.DEBUG)
    logging.getLogger('app.services.vector_service').setLevel(logging.DEBUG)