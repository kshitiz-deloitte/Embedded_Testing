import inspect
import logging


class BaseClass:

    def get_logger(self):
        logger_name = inspect.stack()[1][3]
        log = logging.getLogger(logger_name)
        file_handler = logging.FileHandler("logger.log")
        log_format = logging.Formatter("%(asctime)s :%(levelname)s : %(name)s : %(message)s")
        file_handler.setFormatter(log_format)
        log.addHandler(file_handler)
        log.setLevel(logging.DEBUG)
        return log
