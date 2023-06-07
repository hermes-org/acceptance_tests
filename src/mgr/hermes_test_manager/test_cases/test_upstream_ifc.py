"""Test cases for the upstream connection of an IPC-Hermes-9852 interface.
    
        >>>> Board transport direction >>>>
        ----------+          +----------
           this   |          |  System
           code   | -------> |  under
                  |          |  test
        ----------+          +----------
        thus a downstream connection is used by this test code 
        to receive messages from the system under test.
"""

import re

from callback_tags import CbEvt
from test_cases import hermes_testcase, create_downstream_context, EnvironmentManager

from ipc_hermes.messages import Tag, Message, TransferState, NotificationCode, SeverityType
from ipc_hermes.connections import ConnectionLost


@hermes_testcase
def test_start_shutdown_n_times():
    """Test start and shutdown server 10 times. Ignore any ServiceDescription received.
        Warning: this test may take a minute to complete."""
    for _ in range(10):
        with create_downstream_context():
            pass


@hermes_testcase
def test_exchange_service_description_shutdown_n_times():
    """Test connect and disconnect n times.
       Exchange ServiceDescription and shutdown server.
       Warning: this test may take a minute to complete.
    """
    for _ in range(10):
        with create_downstream_context() as ctxt:
            env = EnvironmentManager()
            env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
            ctxt.expect_message(Tag.SERVICE_DESCRIPTION)


@hermes_testcase
def test_start_handshake_shutdown():
    """Test start server, receive ServiceDescription, shutdown."""
    with create_downstream_context() as ctxt:
        env = EnvironmentManager()
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
        msg = ctxt.expect_message(Tag.SERVICE_DESCRIPTION)
        # check Version is present & correct
        hermes_version = msg.data.get('Version')
        assert hermes_version is not None, 'IPC-Hermes version is missing in ServiceDescription'
        env.run_callback(CbEvt.HERMES_VERSION, version=hermes_version)
        env.log.info('System under test states IPC-Hermes version %s', hermes_version)
        version_regexp = r'^[1-9][0-9]{0,2}\.[0-9]{1,3}$'
        assert re.match(version_regexp, hermes_version), \
            'IPC-Hermes version in ServiceDescription has not in correct format xxx.yyy'
        # check MachineId is present
        machine_id = msg.data.get('MachineId')
        assert machine_id is not None, 'MachineId is missing in ServiceDescription'
        if len(machine_id.strip()) == 0:
            env.run_callback(CbEvt.WARNING,
                             text = 'Be kind to loggers, don\'t leave MachineId in ServiceDescription as empty string')
        # check LaneId is present and non-zero
        received_lane_id = msg.data.get('LaneId')
        assert received_lane_id is not None, 'LaneId is missing in ServiceDescription'
        assert str(received_lane_id).isnumeric and int(received_lane_id) > 0, \
            'LaneId in ServiceDescription is not greater than zero'


@hermes_testcase
def test_terminate_on_wrong_message_in_not_available_not_ready2():
    """Test that connection is closed and reset when wrong messages are recieved
       in state: NotAvailableNotReady
       each sub-test start with handshake and ends with closing the connection
       RevokeMachineReady, StartTransport & StopTransport are not tested as 
       they should never be sent
    """
    env = EnvironmentManager()
    messages = [env.service_description_message(),
                Message.RevokeBoardAvailable(),
                Message.TransportFinished(TransferState.COMPLETE, "some_guid"),
                ]

    for illegal_msg in messages:
        env.log.debug("Sub-test: %s", illegal_msg.tag)
        with create_downstream_context(handshake=True) as ctxt:
            ctxt.send_msg(illegal_msg)
            # now we expect a notification, callback has no purpose here, this must be automatic
            notification = ctxt.expect_message(Tag.NOTIFICATION)
            assert notification.data.get('NotificationCode') == NotificationCode.PROTOCOL_ERROR, \
                'NotificationCode should be 1 (Protocol error)'
            if notification.data.get('Severity') != SeverityType.FATAL:
                env.run_callback(CbEvt.WARNING,
                                 text = f"Notification was sent according to standard, but its recommended to use 'Severity' 1 (Fatal error), recieved {notification.data.get('Severity')}")

            # other end has to close connection so check if socked is dead now
            try:
                ctxt.send_msg(Message.Notification(NotificationCode.MACHINE_SHUTDOWN,
                                                   SeverityType.INFORMATION,
                                                   "this should fail"))
                assert False, f"Upstream did not close connection as expected after: {illegal_msg.tag}"
            except ConnectionLost:
                pass

        env.log.info("Passed sub-test: %s", illegal_msg.tag)
