def setup_logger():
    import logging

    # Create a logger
    logger = logging.getLogger("ChatAppLogger")
    logger.setLevel(logging.DEBUG)

    # Create a file handler
    fh = logging.FileHandler("chat_app.log")
    fh.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to handlers
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

# Initialize the logger
logger = setup_logger()

# Example usage
logger.info("Logger initialized for the chat application.")
logger.debug("This is a debug message.")
logger.error("This is an error message.")

