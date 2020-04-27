import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

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
                   type = None, 
                   id = None):
        self = cls(None, "CheckAlive")
        self.__set("Type", type)
        self.__set("Id", id)
        return self

    @classmethod
    def ServiceDescription(cls, 
                           machine_id, 
                           lane_id, 
                           interface_id = None, 
                           version = "1.2", 
                           supported_features = []):        
        self = cls(None, "ServiceDescription")
        self.__set("MachineId", machine_id)
        self.__set("LaneId", lane_id)
        self.__set("Version", version)
        self.__set("InterfaceId", interface_id)
        supported = ET.SubElement(self._data, "SupportedFeatures")
        for feature in supported_features:
            ET.SubElement(supported, feature)
        return self  
    
    @classmethod
    def Notification(cls, notification_code, severity, description):
        self = cls(None, "Notification")
        self.__set("NotificationCode", notification_code)
        self.__set("Severity", severity)
        self.__set("Description", description)
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
        self.__set("BoardId", board_id)
        self.__set("BoardIdCreatedBy", board_id_created_by)
        self.__set("ProductTypeId", product_type_id)
        self.__set("FailedBoard", failed_board)
        self.__set("ProductTypeId", product_type_id)
        self.__set("FlippedBoard", flipped_board)
        self.__set("TopBarcode", top_barcode)
        self.__set("BottomBarcode", bottom_barcode)
        self.__set("Length", length)
        self.__set("Width", width)
        self.__set("Thickness", thickness)
        self.__set("ConveyorSpeed", conveyor_speed)        
        self.__set("TopClearanceHeight", top_clearance_height)
        self.__set("BottomClearanceHeight", bottom_clearance_height)
        self.__set("Weight", weight)
        self.__set("WorkOrderId", work_order_id)
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
        self.__set("FailedBoard", failed_board)
        self.__set("ForecastId", forecast_id)
        self.__set("BoardId", board_id)
        self.__set("ProductTypeId", product_type_id)
        self.__set("FlippedBoard", flipped_board)
        self.__set("Length", length)
        self.__set("Width", width)
        self.__set("Thickness", thickness)
        self.__set("ConveyorSpeed", conveyor_speed)        
        self.__set("TopClearanceHeight", top_clearance_height)
        self.__set("BottomClearanceHeight", bottom_clearance_height)
        self.__set("Weight", weight)
        self.__set("WorkOrderId", work_order_id)
        return self  

    @classmethod
    def RevokeMachineReady(cls):
        self = cls(None, "RevokeMachineReady")
        return self

    def __set(self, name, value):
        if value is not None:
            self._data.set(name, str(value))
