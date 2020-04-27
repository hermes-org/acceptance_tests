from errors import StateMachineError
from common_types import State
from common_types import MsgType

class UpstreamStateMachine:

    class State:
        def on(self, msg):
            pass

    class NotConnected(State):
        pass

    def __init__(self):
        self._state = self.NotConnected()




    def on(self, msg):
        self._state = self._state.on(msg)

    
