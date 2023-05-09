"""Test cases for the upstream connection of a IPC-Hermes-9852 interface."""

import pytest

from test_cases import hermes_testcase, EnvironmentManager

@hermes_testcase
def test1():
    """Test 1."""
    print('test1')
    assert True

def test2():
    """Test 2."""
    print('test2')
    assert True

@pytest.mark.skip(reason="no way of currently testing this")
@hermes_testcase
def test3():
    """Test 3."""
    print('test3')
    assert False

def test4():
    """Test 4."""
    EnvironmentManager().run_callback()
    print('test4')
    assert True
