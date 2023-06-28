"""Validators for message fields shared by multiple test cases."""

import re
from enum import IntEnum

from callback_tags import CbEvt
from test_cases import EnvironmentManager

from ipc_hermes.messages import Message, NotificationCode, SeverityType
from ipc_hermes import messages

def validate_service_description(env: EnvironmentManager, msg: Message) -> str:
    """Validate a received ServiceDescription message
       and return the Hermes version.
    """
    # Hermes Version (mandatory) is present & correct format
    hermes_version = msg.data.get('Version')
    assert hermes_version is not None, 'IPC-Hermes version is missing in ServiceDescription'
    env.run_callback(CbEvt.HERMES_VERSION, version=hermes_version)
    env.log.info('System under test states IPC-Hermes version %s', hermes_version)
    version_regexp = r'^[1-9][0-9]{0,2}\.[0-9]{1,3}$'
    assert re.match(version_regexp, hermes_version), \
        'IPC-Hermes version in ServiceDescription has not in correct format xxx.yyy, found: ' + hermes_version

    # MachineId (mandatory) is present
    machine_id = msg.data.get('MachineId')
    assert machine_id is not None, 'MachineId is missing in ServiceDescription'
    if len(machine_id.strip()) == 0:
        env.run_callback(CbEvt.WARNING,
                         text = 'Be kind to loggers, don\'t leave MachineId in ServiceDescription as empty string')

    # LaneId (mandatory) is present and larger than zero
    received_lane_id = msg.data.get('LaneId')
    assert received_lane_id is not None, 'LaneId is missing in ServiceDescription'
    assert str(received_lane_id).isnumeric() and int(received_lane_id) > 0, \
        'LaneId in ServiceDescription is not greater than zero'
    if received_lane_id != env.lane_id:
        env.run_callback(CbEvt.WARNING,
                         text = f"Received LaneId ({received_lane_id}) in ServiceDescription, not same as test manager configuration ({env.lane_id}).")
    return hermes_version


def validate_notification(env: EnvironmentManager, msg: Message,
                          expected_type: NotificationCode,
                          expected_severity: SeverityType):
    """Validate a received Notification message"""
    code = _validate_mandatory_enum(env, msg, 'NotificationCode', messages.NotificationCode)
    assert code == expected_type, 'NotificationCode should be ' + expected_type.value + ' ' + expected_type

    severity = _validate_mandatory_enum(env, msg, 'Severity', messages.SeverityType)
    if severity != expected_severity:
        env.run_callback(CbEvt.WARNING,
                            text = f"Notification was sent according to standard, but its recommended to use Severity {expected_severity}:{expected_severity.name}, recieved {severity}")


def validate_board_info(env: EnvironmentManager, msg: Message):
    """Validate a board info in a received message e.g., BoardAvailable"""
    # BoardId (mandatory) is present and correct
    boardid = msg.data.get('BoardId')
    assert boardid is not None, 'Mandatory BoardId is missing in board info'
    boardid_regexp = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    assert re.match(boardid_regexp, boardid), \
        'BoardId has not correct GUID format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx, found: ' + boardid

    # BoardIdCreatedBy (mandatory) is present and non-empty
    boardid_created_by = msg.data.get('BoardIdCreatedBy')
    assert boardid_created_by is not None, 'Mandatory BoardIdCreatedBy is missing in board info'
    assert len(boardid_created_by.strip()) > 0, 'BoardIdCreatedBy is present but empty string in board info'

    # FailedBoard (mandatory) is present and of correct type
    _validate_mandatory_enum(env, msg, 'FailedBoard', messages.BoardQuality)

    # FlippedBoard (mandatory) is present and of correct type
    _validate_mandatory_enum(env, msg, 'FlippedBoard', messages.FlippedBoard)

    # ProductTypeId (optional) if present ??


    # TopBarcode (optional) is present and correct
    _validate_barcode(env, msg, 'TopBarcode')

    # BottomBarcode (optional) is present and correct
    _validate_barcode(env, msg, 'BottomBarcode')

    # Length (optional) if present a positive float
    _validate_float(env, msg, 'Length', max_warning=2000, min_warning=2)

    # Width (optional) if present a positive float
    _validate_float(env, msg, 'Width', max_warning=2000, min_warning=2)

    # Thickness (optional) if present a positive float
    _validate_float(env, msg, 'Thickness', max_warning=100, min_warning=0.1)

    # ConveyerSpeed (optional) if present a positive float
    _validate_float(env, msg, 'ConveyerSpeed', max_warning=600, min_warning=6)

    # TopClearanceHeight (optional) if present a positive float
    _validate_float(env, msg, 'TopClearanceHeight', max_warning=100)

    # BottomClearanceHeight (optional) if present a positive float
    _validate_float(env, msg, 'BottomClearanceHeight', max_warning=100)

    # (v1.1) Weight (optional) if present a positive float
    _validate_float(env, msg, 'Weight', max_warning=10000, min_warning=1)

    # (v1.2) WorkOrderId (optional) if present ??

    # (v1.3) BatchId (optional) if present ??

    # (v1.4) Route (optional) if present an integer between 0 and 65535

    # (v1.4) Action (optional) if present an integer between 0 and 65535

    # (v1.4) SubBoards (optional) if present an array of SB



def _validate_mandatory_enum(_: EnvironmentManager, msg: Message,
                             field_name: str, enum_type: IntEnum) -> int:
    """Validate an manatory enum arg in a received message."""
    field_value = msg.data.get(field_name)
    assert field_value is not None, f"Mandatory {field_name} is missing in {msg.tag}"
    assert str(field_value).isnumeric(), \
        f"{field_name} enum value in {msg.tag} is not an integer, found: {field_value}"
    assert isinstance(enum_type(int(field_value)), enum_type), \
        f"{field_name} enum value in {msg.tag} is not valid, found: {field_value}"
    return int(field_value)


def _validate_barcode(env: EnvironmentManager, msg: Message, barcode_type: str):
    """Validate an optional barcode arg in a received message."""
    barcode = msg.data.get(barcode_type)
    if barcode is None:
        return
    if len(barcode.strip()) == 0:
        env.run_callback(CbEvt.WARNING,
                         text = f"Barcode {barcode_type} in board info is empty string")
    if 'error' in barcode.lower():
        env.run_callback(CbEvt.WARNING,
                         text = f"Barcode {barcode_type} in board info has text 'error' in it")


def _validate_float(env: EnvironmentManager, msg: Message, field_name: str,
                    max_warning: float = None, min_warning: float = None):
    """Validate an optional float arg in a received message."""
    field_value = msg.data.get(field_name)
    if field_value is None:
        return

    assert str(field_value).isnumeric() and float(field_value) > 0, \
        field_name + ' in board info is not positive float'
    max_decimals = 2
    if len(str(field_value).split('.')[1]) <= max_decimals:
        env.run_callback(CbEvt.WARNING,
                         text = f"{field_name} in board info has more than {max_decimals} decimals")
    if min_warning is not None and float(field_value) < min_warning:
        env.run_callback(CbEvt.WARNING,
                         text = f"{field_name} in board info is smaller than {min_warning}, found: {field_value}")
    if max_warning is not None and float(field_value) > max_warning:
        env.run_callback(CbEvt.WARNING,
                         text = f"{field_name} in board info is larger than {max_warning}, found: {field_value}")
