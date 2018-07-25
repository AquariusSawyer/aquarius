import logging


class Loggersettings:

    class Settings:
        formatter = '[%(asctime)s] [%(levelname)s] [%(name)s: %(filename)s-%(lineno)d: %(funcName)s] %(message)s'
        simple_formater = '[%(asctime)s] %(message)s'

    def __init__(self, levelname=logging.DEBUG):
        self.levelname = levelname

    def output_handler(self, levelname=None, formatter_str=None):

        level = levelname
        formatter = logging.Formatter(formatter_str) if formatter_str else logging.Formatter(self.Settings.formatter)

        s = logging.StreamHandler()
        s.setFormatter(formatter)
        s.setLevel(level)
        return s

    def set(self, logger_module=None, handlers=None, hlevelname="DEBUG", formatter=None):
        logger_module = logger_module if logger_module else __name__
        handlers = handlers if handlers else self.output_handler(levelname=hlevelname, formatter_str=formatter)

        Logger = logging.getLogger(logger_module)

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