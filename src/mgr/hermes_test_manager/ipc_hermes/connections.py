"""Connection classes for IPC-Hermes-9852 interface."""

import socket
import logging
import collections
from datetime import datetime
import xml.etree.ElementTree as ET

from ipc_hermes.messages import Message, Tag
from ipc_hermes.state_machine import UpstreamStateMachine

SOCKET_TIMEOUT = 1.0
RECEIVE_TIMEOUT = 60.0
BUFFERSIZE = 4096
ENDTAG = b"</Hermes>"

class ConnectionLost(Exception):
    """Socket connection lost or timed out"""

class UpstreamConnection:
    """Connection class for upstream IPC-Hermes-9852 interface."""

    def __init__(self):
        self._deque = collections.deque()
        self._pending_bytes = b''
        self._socket = None
        self._state_machine = None
        self._log = logging.getLogger('ipc_hermes')

    def connect(self, host:str, port:str|int) -> None:
        """Create a new connection."""
        new_socket = None
        caught_exc = None
        try:
            for resolved in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
                family, socktype, proto, _, sockaddr = resolved
                try:
                    new_socket = socket.socket(family, socktype, proto)
                except OSError as exc:
                    new_socket = None
                    caught_exc = exc
                    continue
                try:
                    new_socket.settimeout(SOCKET_TIMEOUT)
                    new_socket.connect(sockaddr)
                    break
                except OSError as exc:
                    new_socket.close()
                    new_socket = None
                    caught_exc = exc
                    continue
        except OSError as exc:
            # catching getaddrinfo issues e.g. misspelled hostname
            caught_exc = exc

        if new_socket is None:
            raise ConnectionLost(f"Cannot connect to {host}:{port} - {caught_exc}") from caught_exc

        self._state_machine = UpstreamStateMachine()
        self._socket = new_socket
        self._log.debug('Connection to downstream interface successfully opened: %s:%s', host, port)


    def close(self):
        """Close the connection."""
        if self._socket is not None:
            self._socket.close()
            self._log.debug('Connection to downstream interface closed')

    def receive_data(self):
        """Call recv(0) on the socket to trigger a read event."""
        self._socket.recv(0)

    def send_msg(self, msg:Message):
        """Send a message to the downstream interface."""
        self._log.debug('Sending: %s', msg.tag)
        self._state_machine.on_send_tag(msg.tag)
        return self._socket.send(msg.to_bytes())

    def send_tag_and_bytes(self, tag:Tag, msg_bytes:bytes):
        """Send a byte message to the downstream interface. 
           For testing only."""
        self._log.debug('Sending bytes: %s', tag)
        self._state_machine.on_send_tag(tag)
        return self._socket.send(msg_bytes)

    def expect_message(self, tag, timeout_secs=RECEIVE_TIMEOUT):
        """Wait for a message with the given tag while ignoring other messages.
           For testing only.
        """
        self._log.debug('Waiting for: %s', tag)
        start_time = datetime.now()
        while True:
            # if message is in queue, then return it
            while len(self._deque):
                msg = self._deque.popleft()
                if msg.tag == tag:
                    return msg
            # queue is exhausted, so now wait for new/more messages
            try:
                has_received = self._get_next_message()
                if not has_received:
                    raise ConnectionLost(f"Socket was closed before expected message <{tag}> arrived")

            except socket.timeout as exc:
                now = datetime.now()
                delta = now - start_time
                if delta.total_seconds() > timeout_secs:
                    raise ConnectionLost(f"Expected message <{tag}>, but timed out after {timeout_secs} seconds") from exc

    def _get_next_message(self):
        """Get the next message from the socket."""
        while True:
            received = self._socket.recv(BUFFERSIZE)
            if not received:
                return False
            self._pending_bytes += received

            while True:
                index = self._pending_bytes.find(ENDTAG)
                if index == -1:
                    break
                splitat = index + len(ENDTAG)
                msg_bytes, self._pending_bytes = self._pending_bytes[:splitat], self._pending_bytes[splitat:0]
                msg = Message(ET.fromstring(msg_bytes))
                self._log.debug('Received: %s', msg.tag)
                self._state_machine.on_recv(msg)
                self._deque.append(msg)

            if len(self._deque):
                return True
