"""Connection classes for IPC-Hermes-9852 interface."""


import time
import logging
import threading
import collections
import socket
import selectors
import xml.etree.ElementTree as ET
from datetime import datetime

from ipc_hermes.messages import Message, Tag, NotificationCode, SeverityType
from ipc_hermes.state_machine import UpstreamStateMachine, DownstreamStateMachine

SOCKET_TIMEOUT = 20.0
RECEIVE_TIMEOUT = 20.0
BUFFERSIZE = 4096
ENDTAG = b"</Hermes>"

if hasattr(selectors, 'PollSelector'):
    _ServerSelector = selectors.PollSelector
else:
    _ServerSelector = selectors.SelectSelector


class ConnectionLost(Exception):
    """Socket connection lost or timed out"""


class ClientServer:
    """Base class for client and server."""
    def __init__(self):
        self._socket = None
        self._state_machine = None
        self._pending_bytes = b''
        self._deque = collections.deque()
        self._log = logging.getLogger('ipc_hermes')
        self.__shutdown_request = False
        self.__is_shut_down = threading.Event()
        self._receive_thread = None
        self._selector = _ServerSelector()
        self._listener_exception = None

    def connect(self, host:str, port:str|int) -> None:
        """Initiate the connection. To be overridden by subclasses."""

    def close(self) -> None:
        """Stop the receiving threads. Close the connection."""
        self._log.debug('Shutting down connection socket')
        if self._receive_thread is not None:
            self.__shutdown_request = True
            self.__is_shut_down.wait()
        self._selector.close()
        if self._socket is not None:
            self._socket.close()
            self._log.debug('Connection socket closed')

    def send_msg(self, msg:Message) -> int:
        """Send a message."""
        assert self._socket is not None, 'No connection established'
        self._log.debug('Try send: %s', str(msg))
        return self._send_bytes(msg.tag, msg.to_bytes())

    def send_tag_and_bytes(self, tag:Tag, msg_bytes:bytes) -> int:
        """Send a byte message to the downstream interface. 
           Allows protocol violations to be created, for testing only."""
        assert self._socket is not None, 'No connection established'
        self._log.debug('Try send %s bytes, "%s"', len(msg_bytes), tag)
        return self._send_bytes(tag, msg_bytes)

    def _send_bytes(self, tag:Tag, msg_bytes:bytes) -> int:
        """Send a byte message to the downstream interface."""
        self._state_machine.on_send_tag(tag)
        bytes_sent = self._socket.send(msg_bytes)
        time.sleep(0.02)
        if self._listener_exception is not None:
            raise ConnectionLost('Listener exception', self._listener_exception)
        return bytes_sent

    def expect_message(self, tag, timeout_secs=RECEIVE_TIMEOUT) -> Message:
        """Wait for a message with the given tag while ignoring other messages.
           Assumes that another thread is inserting incomming messages into the deque.
        """
        self._log.debug('Wait for expected message: %s', tag)
        start_time = datetime.now()
        while True:
            # if message is in queue, then return it
            while len(self._deque):
                msg = self._deque.popleft()
                self._state_machine.on_recv(msg)
                if msg.tag == tag:
                    self._log.debug('Received expected message: %s', msg.tag)
                    return msg
            # queue is exhausted, so now wait for new/more messages
            time.sleep(0.1)
            now = datetime.now()
            delta = now - start_time
            if delta.total_seconds() > timeout_secs:
                self._log.debug('Timed out after %ss waiting for message: %s', timeout_secs, tag)
                raise ConnectionLost(f"Expected message <{tag}>, but timed out after {timeout_secs} seconds")

    def _start_receiving(self) -> None:
        """Start the receiving thread."""
        assert len(self._selector.get_map()) > 0, 'No connection registered'
        assert self._receive_thread is None, 'Receiving thread already running'
        self._receive_thread = threading.Thread(target=self._listening_loop)
        self._receive_thread.daemon = True
        self._receive_thread.start()
        self._log.debug('Receiving thread started')

    def _listening_loop(self) -> None:
        """Listen for incoming messages. Could be new connections or messages on
           existing connections. The socket should be registered with the handling
           function as data. It will be called with the socket as argument.
        """
        self.__is_shut_down.clear()
        try:
            while not self.__shutdown_request:
                events = self._selector.select(0.5)
                if self.__shutdown_request:
                    # shutdown() called during select(), exit immediately.
                    break
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except IOError as exc:
            self._log.debug('IOError in listening loop: %s', exc)
            self._listener_exception = exc
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()
            self._log.debug('Exiting listening loop')

    def _handle_received_message(self, sock:socket) -> None:
        """Receive messages from the socket and put them in the servers deque."""
        received = sock.recv(BUFFERSIZE)
        self._pending_bytes += received
        while True:
            index = self._pending_bytes.find(ENDTAG)
            if index == -1:
                break
            splitat = index + len(ENDTAG)
            msg_bytes, self._pending_bytes = self._pending_bytes[:splitat], self._pending_bytes[splitat:0]
            msg = Message(ET.fromstring(msg_bytes))
            self._log.debug('Received: %s', msg)
            self._deque.append(msg)


class UpstreamConnection(ClientServer):
    """Creating a connection from upstream client to a downstream IPC-Hermes-9852 server."""

    def connect(self, host:str, port:str|int) -> None:
        """Initiate the upstream connection."""
        new_socket = None
        caught_exc = None
        self._log.debug('Trying to open connection to downstream server: %s:%s', host, port)
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
        self._log.debug('Connection to downstream server successfully opened: %s:%s', host, port)

    def start_receiving(self) -> None:
        """Start the receiving thread."""
        self._selector.register(self._socket, selectors.EVENT_READ, self._handle_received_message)
        super()._start_receiving()


class DownstreamConnection(ClientServer):
    """Creating a downstream server to allow multiple async connections
       from upstream IPC-Hermes-9852 clients. Only one will be allowed though.
    """
    def __init__(self):
        self._server_socket = None
        self._client_address = None
        super().__init__()

    def connect(self, host:str, port:str|int) -> None:
        """Start the downstream server. Get ready to accept connections
           Allow reuse address to be able to instantly move to next test
           without waiting for timeout.
        """
        address = (host, port)
        self._log.debug('Trying to start a downstream server: %s', address)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(address)
        self._server_socket.listen(5)
        self._log.debug('Server listening')

        self._server_socket.setblocking(False)
        self._selector.register(self._server_socket, selectors.EVENT_READ, self._handle_accept)
        self._state_machine = DownstreamStateMachine()
        super()._start_receiving()
        self._log.debug('Downstream server successfully started')

    def wait_for_connection(self, timeout_secs=SOCKET_TIMEOUT) -> str:
        """Wait for a connection to the downstream server.
           _socket will be set from listening thread and handle_accept.
        """
        self._log.debug('Waiting for upstream client to connect')
        start_time = datetime.now()
        while self._socket is None:
            now = datetime.now()
            delta = now - start_time
            if delta.total_seconds() > timeout_secs:
                self._log.debug('Timeout waiting for upstream client')
                raise ConnectionLost(f"Upstream client did not connect within {timeout_secs} seconds")
            time.sleep(0.1)
        self._log.debug('Upstream client connected after %s seconds', delta.total_seconds())
        return str(self._client_address)


    def _handle_accept(self, sock:socket) -> None:
        """The IPC-Hermes-9852 protocol only allows one client.
           So, accept the first and deny all others by sending a Notificaion.
        """
        request, client_address = sock.accept()
        self._log.debug('Verifying a connection request: %s', client_address)

        if self._socket is None:
            self._socket = request
            self._selector.register(self._socket, selectors.EVENT_READ, self._handle_received_message)
            self._client_address = client_address
            self._log.debug('Upstream socket created')
            return

        self._log.debug('Refuse second connection, already connected')
        msg = Message.Notification(NotificationCode.CONNECTION_REFUSED,
                                   SeverityType.ERROR,
                                   'Connection refused because of an established connection')
        request.send(msg.to_bytes())
        try:
            request.shutdown(socket.SHUT_RDWR)
        finally:
            request.close()

    def close(self) -> None:
        """Stop accepting connections and close the server socket."""
        self._log.debug('Shutting down downstream server socket')
        self._selector.unregister(self._server_socket)
        if self._server_socket is not None:
            self._server_socket.close()
            self._log.debug('Server socket closed')
        super().close()
