"""Event tags used in callback messages"""

from enum import Enum
from enum import unique

@unique
class CbEvt(Enum):
    """Event tags used in callback messages"""
    UNKNOWN = 0
    BEFORE_TEST_CASE = 1
    AFTER_TEST_CASE = 2
    PROGRESS = 3
    WAIT_FOR_MSG = 4
    HERMES_VERSION = 5
    CLIENT_CONNECTED = 6
    WARNING = 7
