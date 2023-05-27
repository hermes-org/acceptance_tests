"""IPC-Hermes-9852 message definitions."""

import xml.etree.ElementTree as ET
from datetime import datetime

MAX_MESSAGE_SIZE = 65536

class Tag:
    """IPC-Hermes-9852 message tags."""
    UNKNOWN = "Unknown"
    CHECK_ALIVE = "CheckAlive"
    SERVICE_DESCRIPTION = "ServiceDescription"
    NOTIFICATION = "Notification"
    BOARD_AVAILABLE = "BoardAvailable"
    REVOKE_BOARD_AVAILABLE = "RevokeBoardAvailable"
    MACHINE_READY = "MachineReady"
    REVOKE_MACHINE_READY = "RevokeMachineReady"
    START_TRANSPORT = "StartTransport"
    STOP_TRANSPORT = "StopTransport"
    TRANSPORT_FINISHED = "TransportFinished"
    BOARD_FORECAST = "BoardForecast"
    QUERY_BOARD_INFO = "QueryBoardInfo"
    SEND_BOARD_INFO = "SendBoardInfo"
    SET_CONFIGURATION = "SetConfiguration"
    GET_CONFIGURATION = "GetConfiguration"
    CURRENT_CONFIGURATION = "CurrentConfiguration"

class NotificationCode:
    PROTOCOL_ERROR = "1"
    CONNECTION_REFUSED = "2"
    CONNECTION_RESET = "3"
    CONFIGURATION_ERROR = "4"
    MACHINE_SHUTDOWN = "5"
    BOARDFORECAST_ERROR = "6"

class SeverityType:
    FATAL = "1"
    ERROR = "2"
    WARNING = "3"
    INFORMATION = "4"

class CheckAliveType:
    PING = 1
    PONG = 2

class BoardQuality:
    UNKNOWN = 0
    ANY = 0
    GOOD = 1
    BAD = 2

class FlippedBoard:
    SIDE_UP_IS_UKNOWN = 0
    TOP_SIDE_IS_UP = 1
    BOTTOM_SIDE_IS_UP = 2

class TransferState:
    NOT_STARTED = 1
    INCOMPLETE = 2
    COMPLETE = 3

class Message:
    def __init__(self, xml_root, tag = None):
        if tag is None:
            self._root = xml_root
            self._data = xml_root[0]
            return

        root = ET.Element("Hermes")
        now = datetime.now()
        root.set('Timestamp', now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
        self._root = root
        self._data = ET.SubElement(root, tag)

    @property
    def xml_root(self):
        return self._root

    @property
    def timestamp(self):
        return self._root.get("Timestamp")

    @property
    def data(self):
        return self._data
    @property
    def tag(self):
        return self._data.tag

    def __repr__(self):
        xml_string = ET.tostring(self._root, encoding="unicode") # only unicode encoding returns a string
        return ET.canonicalize(xml_string, strip_text=True)

    def to_bytes(self):
        retval = ET.tostring(self._root) # returns bytes
        return retval

    @classmethod
    def CheckAlive(cls,
                   checkalive_type = None,
                   checkalive_id = None):
        self = cls(None, "CheckAlive")
        self.set("Type", checkalive_type)
        self.set("Id", checkalive_id)
        return self

    @classmethod
    def ServiceDescription(cls,
                           machine_id,
                           lane_id,
                           interface_id = None,
                           version = "1.1",
                           supported_features = None):
        self = cls(None, "ServiceDescription")
        self.set("MachineId", machine_id)
        self.set("LaneId", lane_id)
        self.set("Version", version)
        self.set("InterfaceId", interface_id)
        supported = ET.SubElement(self._data, "SupportedFeatures")
        if supported_features is not None:
            for feature in supported_features:
                ET.SubElement(supported, feature)
        return self

    @classmethod
    def Notification(cls, notification_code, severity, description):
        self = cls(None, "Notification")
        self.set("NotificationCode", notification_code)
        self.set("Severity", severity)
        self.set("Description", description)
        return self

    @classmethod
    def BoardAvailable(cls,
                       board_id,
                       board_id_created_by,
                       failed_board = BoardQuality.UNKNOWN,
                       product_type_id = None,
                       flipped_board = FlippedBoard.SIDE_UP_IS_UKNOWN,
                       top_barcode = None,
                       bottom_barcode = None,
                       length = None,
                       width = None,
                       thickness = None,
                       conveyor_speed = None,
                       top_clearance_height = None,
                       bottom_clearance_height = None,
                       weight = None,
                       work_order_id = None):
        self = cls(None, "BoardAvailable")
        self.set("BoardId", board_id)
        self.set("BoardIdCreatedBy", board_id_created_by)
        self.set("ProductTypeId", product_type_id)
        self.set("FailedBoard", failed_board)
        self.set("ProductTypeId", product_type_id)
        self.set("FlippedBoard", flipped_board)
        self.set("TopBarcode", top_barcode)
        self.set("BottomBarcode", bottom_barcode)
        self.set("Length", length)
        self.set("Width", width)
        self.set("Thickness", thickness)
        self.set("ConveyorSpeed", conveyor_speed)
        self.set("TopClearanceHeight", top_clearance_height)
        self.set("BottomClearanceHeight", bottom_clearance_height)
        self.set("Weight", weight)
        self.set("WorkOrderId", work_order_id)
        return self

    @classmethod
    def BoardForecast(cls,
                      forecast_id = None,
                      time_until_available = None,
                      board_id = None,
                      board_id_created_by = None,
                      failed_board = BoardQuality.UNKNOWN,
                      product_type_id = None,
                      flipped_board = FlippedBoard.SIDE_UP_IS_UKNOWN,
                      top_barcode = None,
                      bottom_barcode = None,
                      length = None,
                      width = None,
                      thickness = None,
                      conveyor_speed = None,
                      top_clearance_height = None,
                      bottom_clearance_height = None,
                      weight = None,
                      work_order_id = None):
        self = cls(None, Tag.BOARD_FORECAST)
        self.set("ForecastId", forecast_id)
        self.set("TimeUntilAvailable", time_until_available)
        self.set("BoardId", board_id)
        self.set("BoardIdCreatedBy", board_id_created_by)
        self.set("ProductTypeId", product_type_id)
        self.set("FailedBoard", failed_board)
        self.set("ProductTypeId", product_type_id)
        self.set("FlippedBoard", flipped_board)
        self.set("TopBarcode", top_barcode)
        self.set("BottomBarcode", bottom_barcode)
        self.set("Length", length)
        self.set("Width", width)
        self.set("Thickness", thickness)
        self.set("ConveyorSpeed", conveyor_speed)
        self.set("TopClearanceHeight", top_clearance_height)
        self.set("BottomClearanceHeight", bottom_clearance_height)
        self.set("Weight", weight)
        self.set("WorkOrderId", work_order_id)
        return self

    @classmethod
    def RevokeBoardAvailable(cls):
        self = cls(None, "RevokeBoardAvailable")
        return self

    @classmethod
    def MachineReady(cls,
                     failed_board = BoardQuality.ANY,
                     forecast_id = None,
                     board_id = None,
                     product_type_id = None,
                     flipped_board = FlippedBoard.SIDE_UP_IS_UKNOWN,
                     length = None,
                     width = None,
                     thickness = None,
                     conveyor_speed = None,
                     top_clearance_height = None,
                     bottom_clearance_height = None,
                     weight = None,
                     work_order_id = None):
        self = cls(None, "MachineReady")
        self.set("FailedBoard", failed_board)
        self.set("ForecastId", forecast_id)
        self.set("BoardId", board_id)
        self.set("ProductTypeId", product_type_id)
        self.set("FlippedBoard", flipped_board)
        self.set("Length", length)
        self.set("Width", width)
        self.set("Thickness", thickness)
        self.set("ConveyorSpeed", conveyor_speed)
        self.set("TopClearanceHeight", top_clearance_height)
        self.set("BottomClearanceHeight", bottom_clearance_height)
        self.set("Weight", weight)
        self.set("WorkOrderId", work_order_id)
        return self

    @classmethod
    def RevokeMachineReady(cls):
        self = cls(None, "RevokeMachineReady")
        return self

    @classmethod
    def StartTransport(cls,
                       board_id,
                       conveyor_speed = None):
        self = cls(None, "StartTransport")
        self.set("BoardId", board_id)
        self.set("ConveyorSpeed", conveyor_speed)
        return self

    @classmethod
    def StopTransport(cls,
                      transfer_state,
                      board_id):
        self = cls(None, "StopTransport")
        self.set("TransferState", transfer_state)
        self.set("BoardId", board_id)
        return self

    @classmethod
    def TransportFinished(cls,
                      transfer_state,
                      board_id):
        self = cls(None, "TransportFinished")
        self.set("TransferState", transfer_state)
        self.set("BoardId", board_id)
        return self

    def set(self, name, value):
        if value is not None:
            self._data.set(name, str(value))
