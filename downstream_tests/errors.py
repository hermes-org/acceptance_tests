from datetime import datetime

class TestError(Exception):
    """Basic exception to propagate test failures"""
    def __init__(self, text):
        super().__init__(text)
        self._time = datetime.now()

class ConnectError(TestError):
    """Failure to connect to socket"""

class StateMachineError(TestError):
    """Hermes state machine was violated"""
    def __init__(self, state, msg):
        super().__init__(f"Illegal msg {msg} in state {state}")

class XmlError(TestError):
    """Message contained invalid XML"""

class AssertError(TestError):
    """Test assertion failed"""
    def __init__(self, msg):
        super().__init__(f"Test assertion failed: {msg}")
