""""IPC-Hermes-9852 state machines."""

import logging
from enum import Enum
from enum import unique

from ipc_hermes.messages import Tag, Message

@unique
class State(Enum):
    """IPC-Hermes-9852 horizontal channel state machine states."""
    UNKNOWN = 0
    NOT_CONNECTED = 1
    SERVICE_DESCRIPTION_DOWNSTREAM = 2
    NOT_AVAILABLE_NOT_READY = 3
    BOARD_AVAILABLE = 4
    AVAILABLE_AND_READY = 5
    MACHINE_READY = 6
    TRANSPORTING = 7
    TRANSPORT_FINISHED = 8
    TRANSPORT_STOPPED = 9

# Horizontal channel state transitions from the upstream state machine view
# i.e. how to change when receiving a message tag depinging on current state
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

# Horizontal channel state transitions from the downstream state machine view
# i.e. how to change when receiving a message tag depinging on current state
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


class StateMachineError(Exception):
    """Hermes state machine was violated"""
    def __init__(self, state, msg):
        super().__init__(f"Illegal msg {msg} in state {state}")


class StateMachine:
    """"Generic state machine implementation. You probably want to use
        UpstreamStateMachine or DownstreamStateMachine instead.

    Args:
        test_log (TestLog): The test log.
        send_dict (dict): The send transition dictionary.
        recv_dict (dict): The receive transition dictionary.
    """
    def __init__(self, send_dict, recv_dict):
        self._state = State.NOT_CONNECTED
        self._send_dict = send_dict
        self._recv_dict = recv_dict
        self._log = logging.getLogger('ipc_hermes')

    def state(self):
        """Get the current state."""
        return self._state

    def on_send_tag(self, tag: str, raise_on_error: bool):
        """Handle a send tag. Normally raises StateMachineError if the message is not allowed.
           Argument
                raise_on_error = False will allow messages that violate the protocol.
        """
        state_dict = self._send_dict.get(tag)
        if state_dict is None:
            # Message tag not defined e.g., Notification, don't change the state.
            return

        new_state = state_dict.get(self._state)
        if new_state == self._state:
            # No state change
            return
        if new_state is None:
            # From-state was not defined, illegal message.
            if raise_on_error:
                raise StateMachineError(self._state, tag)
            else:
                self._log.debug('Illegal %s message sent in %s', tag, self._state)
                return
        self._log.info('From: %s, To: %s, Trigger: %s', self._state, new_state, tag)
        self._state = new_state

    def on_recv(self, msg: Message):
        """Handle a recived message. Raises StateMachineError if the message is not allowed."""
        state_dict = self._recv_dict.get(msg.tag)
        if state_dict is None:
            return

        try:
            new_state = state_dict[self._state]
            if new_state == self._state:
                return
            self._log.info('From: %s, To: %s, Trigger: %s', self._state, new_state, msg.tag)
            self._state = new_state

        except KeyError as exc:
            raise StateMachineError(self._state, msg) from exc

class UpstreamStateMachine(StateMachine):
    """"IPC-Hermes-9852 upstream state machine."""
    def __init__(self):
        super().__init__(send_dict=UPSTREAM_TRANSITION_DICT,
                         recv_dict=DOWNSTREAM_TRANSITION_DICT)

class DownstreamStateMachine(StateMachine):
    """"IPC-Hermes-9852 downstream state machine."""
    def __init__(self):
        super().__init__(send_dict=DOWNSTREAM_TRANSITION_DICT,
                         recv_dict=UPSTREAM_TRANSITION_DICT)
