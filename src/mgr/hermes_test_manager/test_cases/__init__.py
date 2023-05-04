"""Test case decorators and callback manager."""

from contextlib import contextmanager
import pytest

from ipc_hermes.connections import UpstreamConnection
from ipc_hermes.messages import Message

SYSTEM_UNDER_TEST_HOST = '127.0.0.1'
SYSTEM_UNDER_TEST_DOWNSTREAM_PORT = 50101

_ALL_TEST_CASES = {}

def hermes_testcase(func):
    """Decorator for test cases. Should be kept clean to not interfere with pytest.

    Args:
        func (function): Test case function to be decorated.

    Returns:
        function: Decorated test case function.
    """
    def wrapper():
        return func()

    func_name = func.__name__
    if _ALL_TEST_CASES.get(func_name) is not None:
        raise NameError(f"Duplicate function declared: {func_name}")
    _ALL_TEST_CASES[func_name] = func
    return wrapper

def get_test_dictionary() -> dict:
    """Get all test cases.
    
    Returns:
        dict: Dictionary of all test cases. {name: function}
    """
    return _ALL_TEST_CASES


class CallbackManager():
    """cc"""
    _instance = None
    _callback = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CallbackManager, cls).__new__(cls)
        return cls._instance

    def set_callback(self, func):
        """cc"""
        self._callback = func

    def is_undefined(self):
        """cc"""
        return self._callback is None

    def run_callback(self, *args, **kwargs):
        """cc"""
        if self._callback is None:
            pytest.skip("missing callback")
        else:
            self._callback(*args, **kwargs)

###############################################################
# context managers

@contextmanager
def create_upstream_context(host=SYSTEM_UNDER_TEST_HOST,
                            port=SYSTEM_UNDER_TEST_DOWNSTREAM_PORT):
    """Create a horizontal channel upstream connection context."""
    connection = UpstreamConnection()
    try:
        connection.connect(host, port)
        yield connection
        connection.close()
    except:
        connection.close()
        raise

@contextmanager
def create_upstream_context_with_handshake(host = "localhost",
                                           port = SYSTEM_UNDER_TEST_DOWNSTREAM_PORT):
    """Create a horizontal channel upstream connection context
        and do the ServiceDescription handshake.
    """
    connection = UpstreamConnection()
    try:
        connection.connect(host, port)
        connection.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        connection.expect_message("ServiceDescription")
        yield connection
        connection.close()
    except:
        connection.close()
        raise
