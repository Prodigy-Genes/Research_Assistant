import logging

def configure_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)