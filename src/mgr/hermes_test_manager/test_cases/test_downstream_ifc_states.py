"""Test cases for the upstream connection of an IPC-Hermes-9852 interface."""

import pytest

from test_cases import hermes_testcase, create_upstream_context_with_handshake
from test_cases import EnvironmentManager
from ipc_hermes.messages import Message, Tag, TransferState, NotificationCode, SeverityType
from ipc_hermes.connections import ConnectionLost

@hermes_testcase
@pytest.mark.testdriver
def test_terminate_on_wrong_message_in_not_available_not_ready():
    """Test that connection is closed and reset when wrong messages are recieved
       in state: NotAvailableNotReady
       each sub-test start with handshake and ends with closing the connection
       RevokeBoardAvailable & TransportFinished are not tested as they should never be sent
    """
    env = EnvironmentManager()
    messages = [env.service_description_message(),
                Message.RevokeMachineReady(),
                Message.StartTransport("some_guid"),
                Message.StopTransport(TransferState.COMPLETE, "some_guid")
                ]

    for illegal_msg in messages:
        env.log.debug("Sub-test: %s", illegal_msg.tag)
        with create_upstream_context_with_handshake() as ctxt:
            ctxt.send_msg(illegal_msg)
            # now we expect a notification, callback has no purpose here, this must be automatic
            notification = ctxt.expect_message(Tag.NOTIFICATION)
            assert notification.data.get('NotificationCode') == NotificationCode.PROTOCOL_ERROR, \
                'NotificationCode should be 1 (Protocol error)'
            # other end has to close connection so check if socked is dead now
            try:
                ctxt.send_msg(Message.Notification(NotificationCode.MACHINE_SHUTDOWN,
                                                   SeverityType.INFORMATION,
                                                   "this should fail"))
                assert False, f"Upstream did not close connection as expected after: {illegal_msg.tag}"
            except ConnectionLost:
                pass

        env.log.info("Passed sub-test: %s", illegal_msg.tag)
