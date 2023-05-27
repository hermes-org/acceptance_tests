"""Test cases for the upstream connection of a IPC-Hermes-9852 interface."""

from test_cases import hermes_testcase, EnvironmentManager

@hermes_testcase
def test1_success():
    """Test 1 - will allways succeed."""
    print('test1')

@hermes_testcase
def test2_fail():
    """Test 2 - will allways fail."""
    print('test2')
    assert False

@hermes_testcase
def test3_callback():
    """Test 3 - uses the callback."""
    print('test3')
    EnvironmentManager().run_callback(__name__, "A callback from test3")
