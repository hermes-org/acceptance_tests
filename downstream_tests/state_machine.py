from errors import StateMachineError
from common_types import State
from messages import *

UPSTREAM_TRANSITION_DICT = {
    Tag.SERVICE_DESCRIPTION: {
        State.NOT_CONNECTED: State.SERVICE_DESCRIPTION_DOWNSTREAM},
    Tag.MACHINE_READY: {
        State.NOT_AVAILABLE_NOT_READY: State.MACHINE_READY,
        State.BOARD_AVAILABLE: State.AVAILABLE_AND_READY},
    Tag.REVOKE_MACHINE_READY: {
        State.MACHINE_READY: State.NOT_AVAILABLE_NOT_READY,
        State.AVAILABLE_AND_READY: State.BOARD_AVAILABLE},
    Tag.START_TRANSPORT: {
        State.AVAILABLE_AND_READY: State.TRANSPORTING,
        State.MACHINE_READY: State.TRANSPORTING},
    Tag.STOP_TRANSPORT: {
        State.TRANSPORTING: State.TRANSPORT_STOPPED,
        State.TRANSPORT_FINISHED: State.NOT_AVAILABLE_NOT_READY}
    }

DOWNSTREAM_TRANSITION_DICT = {
    Tag.SERVICE_DESCRIPTION: {
        State.SERVICE_DESCRIPTION_DOWNSTREAM: State.NOT_AVAILABLE_NOT_READY},
    Tag.BOARD_AVAILABLE: {
        State.NOT_AVAILABLE_NOT_READY: State.BOARD_AVAILABLE,
        State.MACHINE_READY: State.AVAILABLE_AND_READY,
        State.TRANSPORTING: State.TRANSPORTING,
        State.TRANSPORT_STOPPED: State.TRANSPORT_STOPPED},
    Tag.REVOKE_BOARD_AVAILABLE: {
        State.BOARD_AVAILABLE: State.NOT_AVAILABLE_NOT_READY,
        State.AVAILABLE_AND_READY: State.MACHINE_READY,
        State.TRANSPORTING: State.TRANSPORTING,
        State.TRANSPORT_STOPPED: State.TRANSPORT_STOPPED},
    Tag.TRANSPORT_FINISHED: {
        State.TRANSPORTING: State.TRANSPORT_FINISHED,
        State.TRANSPORT_STOPPED: State.NOT_AVAILABLE_NOT_READY},
    Tag.BOARD_FORECAST: {
        State.NOT_AVAILABLE_NOT_READY: State.NOT_AVAILABLE_NOT_READY,
        State.MACHINE_READY: State.MACHINE_READY,
        State.TRANSPORTING: State.TRANSPORTING,
        State.TRANSPORT_STOPPED: State.TRANSPORT_STOPPED}
    }

class StateMachine:
    def __init__(self, test_log, send_dict, recv_dict):
        self._state = State.NOT_CONNECTED
        self._test_log = test_log
        self._send_dict = send_dict
        self._recv_dict = recv_dict

    def state(self):
        return self._state

    def on_send_tag(self, tag):
        state_dict = self._send_dict.get(tag)
        if state_dict is None:
            return

        state = state_dict.get(self._state)
        if state is None or state == self._state:
            return

        self._test_log.log_transition(src=self._state, tag=tag, tgt=state)
        self._state = state

    def on_recv(self, msg):
        state_dict = self._recv_dict.get(msg.tag)
        if state_dict is None:
            return

        try:
            state = state_dict[self._state]
            if state == self._state:
                return

            self._test_log.log_transition(src=self._state, tag=msg.tag, tgt=state)
            self._state = state

        except KeyError:
            raise StateMachineError(self._state, msg)

class UpstreamStateMachine(StateMachine):
    def __init__(self, test_log):
        super().__init__(test_log, 
                         send_dict=UPSTREAM_TRANSITION_DICT, 
                         recv_dict=DOWNSTREAM_TRANSITION_DICT)

class DownstreamStateMachine(StateMachine):
    def __init__(self, test_log):
        super().__init__(test_log, 
                         send_dict=DOWNSTREAM_TRANSITION_DICT, 
                         recv_dict=UPSTREAM_TRANSITION_DICT)
