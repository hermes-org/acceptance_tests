"""Test cases for both connections of an IPC-Hermes-9852 interface.
    where interaction with the system under test using the API callback function is required.
    
        >>>> Board transport direction >>>>
        ----------+          +---------+          +----------
           this   |          |  System |          |
           code   | -------> |  under  | -------> | this code
                  |          |  test   |          |
        ----------+          +---------+          +----------
"""
from test_cases import hermes_testcase
from test_cases.test_downstream_ifc_interactive import complete_board_transfer_from_sut
from test_cases.test_upstream_ifc_interactive import complete_bamr_board_transfer_to_sut

@hermes_testcase
def test_pass_through():
    """
    Test a complete board transfer from upstream to downstream unit
    with system under test in the middle.
    Starting with exchanging ServiceDescriptions.

    Sequence: BoardAvailable before MachineReady
    """
    (board_id, _) = complete_bamr_board_transfer_to_sut()
    (recv_board_id, _) = complete_board_transfer_from_sut()

    assert board_id == recv_board_id, "Board ID mismatch"
