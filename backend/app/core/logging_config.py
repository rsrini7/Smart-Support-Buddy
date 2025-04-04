import logging
import sys

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

    # Set levels for specific loggers
    logging.getLogger('app.services.jira_service').setLevel(logging.DEBUG)
    logging.getLogger('app.services.msg_parser').setLevel(logging.DEBUG)
    logging.getLogger('app.services.vector_service').setLevel(logging.DEBUG)