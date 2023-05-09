"""Test cases for the downstream connection of an IPC-Hermes-9852 interface
    where interaction with the system under test using the API callback function is required.

    >>>> Board transport direction >>>>
    ----------+          +----------
       System |          |  this
       under  | -------- |  code
       test   |          |
    ----------+          +----------
    thus an upstream connection is used by this test code 
    to send messages to the system under test.

    The test code does not know which lane interface is used,
    this is controlled by host/port configuration.
"""
from test_cases import hermes_testcase, create_upstream_context_with_handshake
from test_cases import EnvironmentManager
from ipc_hermes.messages import Tag, Message, TransferState


@hermes_testcase
def test_complete_board_transfer_from_sut():
    """Test a complete board transfer. Starting with exchanging ServiceDescriptions."""
    with create_upstream_context_with_handshake() as ctxt:
        # signal that we are ready to receive board
        ctxt.send_msg(Message.MachineReady())

        # ask for external agent to signal board available
        EnvironmentManager().run_callback(__name__,
                                       'Action required: Send BoardAvailable',
                                       msg=Tag.BOARD_AVAILABLE)
        board_available = ctxt.expect_message(Tag.BOARD_AVAILABLE)
        board_id = board_available.data.get('BoardId')

        # signal that transport can start
        ctxt.send_msg(Message.StartTransport(board_id))

        # ask for external agent to send board and signal when board has left upstream
        EnvironmentManager().run_callback(__name__,
                                       "Action required: Send TransportFinished",
                                       msg=Tag.TRANSPORT_FINISHED)
        ctxt.expect_message(Tag.TRANSPORT_FINISHED)

        ctxt.send_msg(Message.StopTransport(TransferState.COMPLETE, board_id))
        ctxt.close()
        assert True
