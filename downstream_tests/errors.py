from datetime import datetime

class TestError(Exception):
    """Basic exception to propagate test failures"""
    def __init__(self, msg):
        super().__init__(msg)
        self._time = datetime.now()

class ConnectError(TestError):
    """Failure to connect to socket"""
    pass

class TimeoutError(TestError):
    """Failure to receive excpected response in time"""
    pass

class StateMachineError(TestError):
    """Hermes state machine was violated"""
    def __init__(self, state, msg):
        super().__init__(f"Illegal msg <{msg}> in state <{state}>")

class XmlError(TestError):
    """Message contained invalid XML"""
    pass

class AssertError(TestError):
    """Test assertion failed"""
    pass



