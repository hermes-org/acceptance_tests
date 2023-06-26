"""Test cases for the upstream connection of a IPC-Hermes-9852 interface."""

from callback_tags import CbEvt
from test_cases import hermes_testcase, EnvironmentManager

@hermes_testcase
def test1_success():
    """Test 1 - will allways succeed."""
    print('test1')

@hermes_testcase
def test2_fail():
    """
    Test 2 - will allways fail.
    Note! This test case is expected to fail.
    """
    print('test2')
    assert False

@hermes_testcase
def test3_callback():
    """
    Test 3 - uses the callback.

    This is a very simple test case that uses the callback but with a verrrrrrrrrrrrrrrrrrrrrry long description.

    * This is bullet 1
    * This is bullet 2
    """
    print('test3')
    EnvironmentManager().run_callback(CbEvt.UNKNOWN, text="A callback from test3")
