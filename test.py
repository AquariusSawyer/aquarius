import logging
from logger import Loggersettings


LS = Loggersettings()
LS.output("aquarius")

Logger = logging.getLogger("aquarius")


Logger.debug(1111)