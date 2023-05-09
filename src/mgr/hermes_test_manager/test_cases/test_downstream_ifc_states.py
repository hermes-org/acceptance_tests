"""Test cases for the upstream connection of an IPC-Hermes-9852 interface."""

import pytest

from test_cases import hermes_testcase, create_upstream_context_with_handshake
from test_cases import EnvironmentManager
from ipc_hermes.messages import Message, Tag, TransferState

@hermes_testcase
@pytest.mark.testdriver
def test_terminate_on_unexpected_revoke_board_available():
    """Test that connection is closed and reset when xxx message are recieved in wrong state"""
    with create_upstream_context_with_handshake() as ctxt:
        ctxt.send_msg(Message.RevokeBoardAvailable())
        # other end has to close connection so check if socked is dead now,
        # optionally a Notification can be sent before closing
        try:
            EnvironmentManager().run_callback(__name__,
                                       'Action required: Send Notification',
                                       msg=Tag.NOTIFICATION)
            ctxt.receive_data()
            ctxt.expect_message(Tag.NOTIFICATION)
            ctxt.close()
            raise ValueError("RevokeBoardAvailable erroneously accepted after handshake")
        except:
            pass
    assert True

@hermes_testcase
@pytest.mark.testdriver
def test_terminate_on_unexpected_revoke_machine_ready():
    """Test that connection is closed and reset when xxx message are recieved in wrong state"""
    with create_upstream_context_with_handshake() as ctxt:
        ctxt.send_msg(Message.RevokeMachineReady())
        # other end has to close connection so check if socked is dead now,
        # optionally a Notification can be sent before closing
        try:
            # TODO: Note that TestDriver automatically sends Notification in this specific case
            EnvironmentManager().run_callback(__name__,
                                       'Action required: Send Notification',
                                       msg=Tag.NOTIFICATION)
            ctxt.receive_data()
            ctxt.expect_message(Tag.NOTIFICATION)
            ctxt.close()
            raise ValueError("RevokeMachineReady erroneously accepted after handshake")
        except:
            pass

@hermes_testcase
@pytest.mark.testdriver
def test_terminate_on_unexpected_transport_finished():
    """Test that connection is closed and reset when xxx message are recieved in wrong state"""
    with create_upstream_context_with_handshake() as ctxt:
        ctxt.send_msg(Message.TransportFinished(TransferState.COMPLETE, "some_guid"))
        # other end has to close connection so check if socked is dead now,
        # optionally a Notification can be sent before closing
        try:
            EnvironmentManager().run_callback(__name__,
                                       'Action required: Send Notification',
                                       msg=Tag.NOTIFICATION)
            ctxt.receive_data()
            ctxt.expect_message(Tag.NOTIFICATION)
            ctxt.close()
            raise ValueError("TransportFinished erroneously accepted after handshake")
        except:
            pass
