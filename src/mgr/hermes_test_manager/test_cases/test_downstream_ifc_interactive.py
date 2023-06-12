"""Test cases for the downstream connection of an IPC-Hermes-9852 interface
    where interaction with the system under test using the API callback function is required.

    >>>> Board transport direction >>>>
    ----------+          +----------
       System |          |  this
       under  | -------> |  code
       test   |          |
    ----------+          +----------
    thus an upstream connection is used by this test code 
    to send messages to the system under test.
"""

from callback_tags import CbEvt
from test_cases import hermes_testcase, create_upstream_context
from test_cases import EnvironmentManager, message_validator

from ipc_hermes.messages import Tag, Message, TransferState


@hermes_testcase
def test_complete_board_transfer_from_sut():
    """Test a complete board transfer. Starting with exchanging ServiceDescriptions."""
    with create_upstream_context(handshake=True) as ctxt:
        env = EnvironmentManager()
        # signal that we are ready to receive board
        ctxt.send_msg(Message.MachineReady())

        # ask for external agent to signal board available
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.BOARD_AVAILABLE)
        msg_board_available = ctxt.expect_message(Tag.BOARD_AVAILABLE)
        message_validator.validate_board_info(env, msg_board_available)
        board_id = msg_board_available.data.get('BoardId')

        # signal that transport can start
        ctxt.send_msg(Message.StartTransport(board_id))

        # ask for external agent to send board and signal when board has left upstream
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.TRANSPORT_FINISHED)
        transport_finished = ctxt.expect_message(Tag.TRANSPORT_FINISHED)
        board_id2 = transport_finished.data.get('BoardId')
        assert board_id == board_id2

        ctxt.send_msg(Message.StopTransport(TransferState.COMPLETE, board_id))
