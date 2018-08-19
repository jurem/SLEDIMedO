import logging

LOGGER_FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S"
LOGGER_FORMAT_LOG = "%(asctime)s [%(levelname)s] %(filename)s: %(message)s"
LOGGER_FORMAT_CONSOLE = "[%(levelname)s] %(message)s"

DEFAULT_LOG_FILE_NAME = "logs.log"
SEPERATE_FILES = False  # will create seperate log files for all the scrapers

def loadLogger(loggerName):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatterLog = logging.Formatter(LOGGER_FORMAT_LOG, LOGGER_FORMAT_DATETIME)
    formatterConsole = logging.Formatter(LOGGER_FORMAT_CONSOLE)

    loggerFileName = DEFAULT_LOG_FILE_NAME
    if SEPERATE_FILES:
        loggerFileName = loggerName.lower()+".log"

    # for logs
    file_handler = logging.FileHandler(loggerFileName)
    file_handler.setFormatter(formatterLog)
    # file_handler.setLevel(logging.ERROR)

    # for normal print in the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatterConsole)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

def setLoggerLevel(logger, level):
    levelDict = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level.upper()
    try:
        logger.setLevel(levelDict[level])
        print ("LEVEL {} SET.".format(level))
        return logger
    except Exception:
        logger.exception("Cannot set logger level {}".format(level))

# LogRecord attributes
# https://docs.python.org/3/library/logging.html#logrecord-attributes

# logging levels:
# DEBUG    : Detailed information, typically of interest only when diagnosing problems.
# INFO     : Confirmation that things are working as expected.
# WARNING  : An indication that something unexpected happened, or indicative of some problem in the
#            near future (e.g. 'disk space low'). The software is still working as expected.
# ERROR    : Due to a more serious problem, the software has not been able to perform some function.
# CRITICAL : A serious error, indicating that the program itself may be unable to continue running.