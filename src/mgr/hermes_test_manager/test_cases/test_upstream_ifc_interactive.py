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

from callback_tags import CbEvt
from test_cases import hermes_testcase, EnvironmentManager
from test_cases import create_downstream_context_with_handshake

from ipc_hermes.messages import Tag, Message, TransferState


@hermes_testcase
def test_complete_mrba_board_transfer_to_sut():
    """Test a complete board transfer to upstream port of system under test.
       Starting with exchanging ServiceDescriptions.

       Sequence: MachineReady before BoardAvailable
    """
    with create_downstream_context_with_handshake() as ctxt:
        env = EnvironmentManager()

        # ask for external agent to signal machine ready
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.MACHINE_READY)
        ctxt.expect_message(Tag.MACHINE_READY)

        # signal that we are ready to send board
        board_id = '1234567890'
        ctxt.send_msg(Message.BoardAvailable(board_id, env.machine_id))

        # ask for external agent to signal start transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.START_TRANSPORT)
        ctxt.expect_message(Tag.START_TRANSPORT)

        # signal that transport is finished
        ctxt.send_msg(Message.TransportFinished(TransferState.COMPLETE, board_id))

        # ask for external agent to send board and signal stop transport
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.STOP_TRANSPORT)
        ctxt.expect_message(Tag.STOP_TRANSPORT)


@hermes_testcase
def test_complete_bamr_board_transfer_to_sut():
    """Test a complete board transfer to upstream port of system under test.
       Starting with exchanging ServiceDescriptions.

       Sequence: BoardAvailable before MachineReady
    """
    with create_downstream_context_with_handshake() as ctxt:
        env = EnvironmentManager()

        # signal that we are ready to send board
        board_id = '1234567890'
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
