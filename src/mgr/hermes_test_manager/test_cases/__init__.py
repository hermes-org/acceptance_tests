"""Test case decorators and callback manager."""

from contextlib import contextmanager
import logging
import pytest

from ipc_hermes.connections import UpstreamConnection, DownstreamConnection
from ipc_hermes.messages import Message, Tag

SYSTEM_UNDER_TEST_HOST = '127.0.0.1'
SYSTEM_UNDER_TEST_PORT = 50101

_ALL_TEST_CASES = {}

def get_log():
    """Return logger for test cases."""
    return logging.getLogger('test_cases')


def hermes_testcase(func):
    """Decorator for test cases. Should be kept clean to not interfere with pytest.

    Args:
        func (function): Test case function to be decorated.

    Returns:
        function: Decorated test case function.
    """
    def wrapper():
        EnvironmentManager().optional_start_of_test_callback()
        retval = func()
        EnvironmentManager().optional_end_of_test_callback()
        return retval

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


class EnvironmentManager():
    """Singelton callback manager for test cases."""
    _instance = None
    _callback = None
    _callback_used = False
    _include_handshake = False
    _machine_id = "Hermes Test API"
    _lane_id = "1"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvironmentManager, cls).__new__(cls)
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
            self._callback_used = True
            self._callback(*args, **kwargs)

    @property
    def include_handshake(self) -> bool:
        """Run callback for the ServeDescription message to remind users of Hermes TestDriver"""
        return self._include_handshake

    @include_handshake.setter
    def include_handshake(self, value:bool):
        self._include_handshake = value

    @property
    def lane_id(self) -> str:
        """Lane ID used in tests"""
        return self._lane_id

    @lane_id.setter
    def lane_id(self, value:str):
        self._lane_id = value

    @property
    def machine_id(self) -> str:
        """Machine ID used in tests"""
        return self._machine_id

    def service_description_message(self) -> Message:
        """Return ServiceDescription message"""
        return Message.ServiceDescription(self.machine_id, self.lane_id)

    def optional_start_of_test_callback(self) -> None:
        """Send optional callback before test is executed
           otherwise just reset callback_used flag
        """
        self._callback_used = False

    def optional_end_of_test_callback(self) -> None:
        """Send a final callback when test is done"""
        if self._callback_used:
            self.run_callback(__name__, 'Done.')


###############################################################
# context managers

@contextmanager
def create_upstream_context(receive=True,
                            host=SYSTEM_UNDER_TEST_HOST,
                            port=SYSTEM_UNDER_TEST_PORT):
    """Create a horizontal channel upstream connection context."""
    connection = UpstreamConnection()
    try:
        connection.connect(host, port)
        if receive:
            connection.start_receiving()
        get_log().debug('Yield connection to test case')
        yield connection
        get_log().debug('Return from test case and yield')
        connection.close()
    except:
        connection.close()
        raise

@contextmanager
def create_upstream_context_with_handshake(host = SYSTEM_UNDER_TEST_HOST,
                                           port = SYSTEM_UNDER_TEST_PORT):
    """Create a horizontal channel upstream connection context
        and do the ServiceDescription handshake.
    """
    connection = UpstreamConnection()
    env = EnvironmentManager()
    try:
        connection.connect(host, port)
        connection.start_receiving()
        connection.send_msg(EnvironmentManager().service_description_message())
        if env.include_handshake:
            env.run_callback(__name__, 'Action required: Send ServiceDescription')
        connection.expect_message(Tag.SERVICE_DESCRIPTION)
        get_log().debug('Yield connection to test case')
        yield connection
        get_log().debug('Return from test case and yield')
        connection.close()
    except:
        connection.close()
        raise

@contextmanager
def create_downstream_context_with_handshake(host = SYSTEM_UNDER_TEST_HOST,
                                             port = SYSTEM_UNDER_TEST_PORT):
    """Create a horizontal channel downstream server context
        and do the ServiceDescription handshake.
    """
    connection = DownstreamConnection()
    env = EnvironmentManager()
    try:
        connection.connect(host, port)
        connection.wait_for_connection(10)
        if env.include_handshake:
            env.run_callback(__name__, 'Action required: Send ServiceDescription')
        connection.expect_message(Tag.SERVICE_DESCRIPTION)
        connection.send_msg(EnvironmentManager().service_description_message())
        get_log().debug('Yield connection to test case')
        yield connection
        get_log().debug('Return from yield and test case')
        connection.close()
    except Exception:
        connection.close()
        raise
