import xml.etree.ElementTree as ET
from datetime import datetime

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
CURRENT_CONFIGURATION = "CurrentConfiguration"

CHECK_ALIVE_PING = 1
CHECK_ALIVE_PONG = 2
UNKNOWN_QUALITY = 0
GOOD_BOARD = 1
FAILED_BOARD = 2

SIDE_UP_UKNOWN = 0
BOARD_TOP_SIDE_UP = 1
BOARD_BOTTOM_SIDE_UP = 2

# def __to_optional_float(value):
#     try:
#         return float(value)
#     except:
#         return None

# def __to_optional_int(value)
#     try:
#         return int(value)
#     except:
#         return None

# class __Data:
#     def __init__(self, xml_data):
#         self._data = xml_data

#     __to_string(self, name):
        

# class CheckAliveData:
#     def __init__(self, xml_data):
#         self._data = xml_data

#     def optional_type(self):
#         return __to_optional_int(self._data.get("Type"))
    
#     def optional_id(self):
#         return self._data.get("Id")

# class ServiceDescriptionData:
#     def __init__(self, xml_data):
#         self._data = xml_data

#     def machine_id(self):
#         return self._data.get("MachineId")

#     def lane_id(self):
#         return self._data.get("LaneId")
    
#     def optional_interface_id(self):
        
#         return self._data.get("InterfaceId")

#     def version(self):
#         return self._data.get("")

# class NotificationData:
#     def __init__(self, xml_data):
#         self._data = xml_data


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
        return ET.tostring(self._root, encoding="unicode") # only unicode encoding returns a string

    def to_bytes(self):
        s = ET.tostring(self._root) # returns bytes
        return s
    
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
                           version = "1.2", 
                           supported_features = None):        
        self = cls(None, "ServiceDescription")
        self.set("MachineId", machine_id)
        self.set("LaneId", lane_id)
        self.set("Version", version)
        self.set("InterfaceId", interface_id)
        supported = ET.SubElement(self._data, "SupportedFeatures")
        if (supported_features is not None):
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
                       failed_board = UNKNOWN_QUALITY,
                       product_type_id = None, 
                       flipped_board = SIDE_UP_UKNOWN,
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
    def RevokeBoardAvailable(cls):
        self = cls(None, "RevokeBoardAvailable")
        return self

    @classmethod
    def MachineReady(cls,
                     failed_board = UNKNOWN_QUALITY,
                     forecast_id = None,
                     board_id = None,
                     product_type_id = None,
                     flipped_board = SIDE_UP_UKNOWN,
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
    def TransportFinished(cls,
                          transfer_state = 1,
                          board_id = None):
        self = cls(None, "TransportFinished")
        self.set("TransferState", transfer_state)
        self.set("BoardId", board_id)
        return self

    @classmethod
    def BoardForecast(cls,
                      failed_board,
                      flipped_board,
                      forecast_id = None,
                      time_until_avail = None,
                      board_id = None,
                      board_id_created_by = None,
                      product_type_id = None,
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
        self = cls(None, "TransportFinished")
        self.set("ForecastId", forecast_id)
        self.set("TimeUntilAvailable", time_until_avail)
        self.set("BoardId", board_id)
        self.set("BoardIdCreatedBy", board_id_created_by)
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

    def set(self, name, value):
        if value is not None:
            self._data.set(name, str(value))
