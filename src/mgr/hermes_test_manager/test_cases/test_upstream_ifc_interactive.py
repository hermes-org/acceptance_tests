"""Test cases for the upstream connection of an IPC-Hermes-9852 interface.
    where interaction with the system under test using the API callback function is required.
    
        >>>> Board transport direction >>>>
        ----------+          +----------
           this   |          |  System
           code   | -------> |  under
                  |          |  test
        ----------+          +----------
        thus a downstream connection is used by this test code 
        to receive messages from the system under test.
"""
import uuid

from callback_tags import CbEvt
from test_cases import hermes_testcase, create_downstream_context, EnvironmentManager

from ipc_hermes.messages import Tag, Message, TransferState


@hermes_testcase
def test_complete_mrba_board_transfer_to_sut():
    """
    Test a complete board transfer to upstream port of system under test.
    Starting with exchanging ServiceDescriptions.

    Sequence: MachineReady before BoardAvailable
    """
    complete_bamr_board_transfer_to_sut()


@hermes_testcase
def test_complete_mrba_board_transfer_to_sut_with_unknown_msg():
    """
    Test a complete board transfer with an unknown message in the sequence.
    The unknown message should be ignored and the sequence should continue.

    It's not allowed to forward the unknown message to other systems,
    this is tested in a separate test case.
    """
    complete_bamr_board_transfer_to_sut(send_unexpected_msg=True)


def complete_bamr_board_transfer_to_sut(send_unexpected_msg=False):
    """
    Actual test code for complete board transfer to upstream port of system under test.
    Returns the board id and the BoardAvailable message for end-2-end testing.
    """
    with create_downstream_context(handshake=True) as ctxt:
        env = EnvironmentManager()

        # ask for external agent to signal machine ready
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.MACHINE_READY)
        ctxt.expect_message(Tag.MACHINE_READY)

        if send_unexpected_msg:
            unknown_msg_bytes = b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsFirstUnknown /></Hermes>"
            ctxt.send_tag_and_bytes(None, unknown_msg_bytes)

        # signal that we are ready to send board
        board_id = str(uuid.uuid4())
        boardavailable_message = Message.BoardAvailable(board_id, env.machine_id)
        ctxt.send_msg(boardavailable_message)

        # ask for external agent to signal start transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.START_TRANSPORT)
        ctxt.expect_message(Tag.START_TRANSPORT)

        if send_unexpected_msg:
            unknown_msg_bytes = b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsSecondUnknown /></Hermes>"
            ctxt.send_tag_and_bytes(None, unknown_msg_bytes)

        # signal that transport is finished
        ctxt.send_msg(Message.TransportFinished(TransferState.COMPLETE, board_id))

        # ask for external agent to send board and signal stop transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.STOP_TRANSPORT)
        ctxt.expect_message(Tag.STOP_TRANSPORT)
        return (board_id, boardavailable_message)


@hermes_testcase
def test_complete_bamr_board_transfer_to_sut():
    """
    Test a complete board transfer to upstream port of system under test.
    Starting with exchanging ServiceDescriptions.

    Sequence: BoardAvailable before MachineReady
    """
    with create_downstream_context(handshake=True) as ctxt:
        env = EnvironmentManager()

        # signal that we are ready to send board
        board_id = str(uuid.uuid4())
        ctxt.send_msg(Message.BoardAvailable(board_id, env.machine_id))

        # ask for external agent to signal machine ready
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.MACHINE_READY)
        ctxt.expect_message(Tag.MACHINE_READY)

        # ask for external agent to signal start transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.START_TRANSPORT)
        ctxt.expect_message(Tag.START_TRANSPORT)

        # signal that transport is finished
        ctxt.send_msg(Message.TransportFinished(TransferState.COMPLETE, board_id))

        # ask for external agent to send board and signal stop transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.STOP_TRANSPORT)
        ctxt.expect_message(Tag.STOP_TRANSPORT)
