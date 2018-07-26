import logging
from json import dumps


__all__ = ['LoggerStr', 'Loggersettings']


def LoggerStr(content, *args, **kwargs):

    if isinstance(content, (dict, list, tuple)):
        return dumps(content, indent=4, *args, **kwargs)

    if isinstance(content, Exception):
        return content.__class__.__name__ + ": " + str(content)

    return content


class Loggersettings:

    class Settings:
        formatter = '[%(asctime)s] [%(levelname)s] [%(name)s: %(filename)s-%(lineno)d: %(funcName)s] %(message)s'
        simple_formater = '[%(asctime)s] %(message)s'

    def __init__(self, levelname=logging.DEBUG):
        self.levelname = levelname

    @classmethod
    def output_handler(cls, levelname=None, formatter_str=None):

        level = levelname
        formatter = logging.Formatter(formatter_str) if formatter_str else logging.Formatter(cls.Settings.formatter)

        s = logging.StreamHandler()
        s.setFormatter(formatter)
        s.setLevel(level)
        return s

    def set_logger(self, logger_name=None, handlers=None, hlevelname="DEBUG", formatter=None):

        logger_name = logger_name if logger_name else __name__
        handlers = handlers if handlers else self.output_handler(levelname=hlevelname, formatter_str=formatter)

        Logger = logging.getLogger(logger_name)

        if not isinstance(handlers, list):

            handlers = [handlers]

        for h in handlers:
            Logger.addHandler(h)

        Logger.setLevel(self.levelname)

    def output(self, name):
        handler = self.output_handler(logging.DEBUG, self.Settings.simple_formater)
        Logger = logging.getLogger(name)
        Logger.addHandler(handler)
        Logger.setLevel(self.levelname)

    @staticmethod
    def get_logger(name):
        return logging.getLogger(name)
