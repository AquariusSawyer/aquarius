import logging
from logger import Loggersettings, LoggerStr


LS = Loggersettings("ERROR")
LS.set_logger("aquarius")

Logger = logging.getLogger("aquarius")

def printf():
    try:
        1/0
    except Exception as e:
        Logger.exception(e)

printf()
