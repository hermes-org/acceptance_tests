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
    """Singelton callback manager for test cases."""
    _instance = None
    _callback = None
    _include_handshake = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CallbackManager, cls).__new__(cls)
        return cls._instance

    def register_callback(self, func):
        """Register a callback function for test cases."""
        self._callback = func

    def is_undefined(self):
        """Check if a callback function is registered."""
        return self._callback is None

    def run_callback(self, *args, **kwargs):
        """Execute the callback function.
           Raise a skip exception if no callback is registered.
        """
        if self._callback is None:
            pytest.skip("missing callback")
        else:
            self._callback(*args, **kwargs)

    @property
    def include_handshake(self) -> bool:
        """Run callback for the ServeDescription message to remind users of Hermes TestDriver"""
        return self._include_handshake

    @include_handshake.setter
    def include_handshake(self, value:bool):
        self._include_handshake = value

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
        if CallbackManager().include_handshake:
            CallbackManager().run_callback(__name__,
                                            'Action required: Send ServiceDescription')

        connection.expect_message("ServiceDescription")
        yield connection
        connection.close()
    except:
        connection.close()
        raise
