from enum import Enum

def State(Enum):
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
    DISCONNECTED = 10

def MsgType(Enum):
    UNKNOWN = "Unknown"
    CHECK_ALIVE = "CheckAlive"
    SERVICE_DESCRIPTION = "ServiceDescription"
    NOTIFICATION = "Notification"
    BOARD_AVAILABLE = "BoardAvailable"
    REVOKE_BOARD_AVAILABLE = "RevokeBoardAvailable"
    MACHINE_READY = "MachineReady"
    REVOKE_MACHINE_READY = "RevokeMachineReady"
    START_TRANSPORT = "TransportReady"
    STOP_TRANSPORT = "StopTransport"
    TRANSPORT_FINISHED = "TransportFinished"
    BOARD_FORECAST = "BoardForecast"
    QUERY_BOARD_INFO = "QuerayBoardInfo"
    SEND_BOARD_INFO = "SendBoardInfo"
    SET_CONFIGURATION = "SetConfiguration"
    GET_CONFIGURATION = "GetConfiguration"
    CURRENT_CONFIGURATION = "CurrenteConfiguration"
