from enum import Enum
from enum import unique

@unique
class State(Enum):
    UNKNOWN = 0
    NOT_CONNECTED = 1
    SERVICE_DESCRIPTION_DOWNSTREAM = 2
    NOT_AVAILABLE_NOT_READY = 3
    BOARD_AVAILABLE = 4
    AVAILABLE_AND_READY = 5
    MACHINE_READY = 6
    TRANSPORTING = 7
    TRANSPORT_FINISHED = 8
    TRANSPORT_STOPPED = 9