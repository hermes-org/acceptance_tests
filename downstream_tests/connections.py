import collections
from datetime import datetime
import socket
import xml.etree.ElementTree as ET

from messages import Message
from state_machine import UpstreamStateMachine

TIMEOUT = 1.0
BUFFERSIZE = 4096
ENDTAG = b"</Hermes>"

class UpstreamConnection:

    def __init__(self, test_log):
        self._deque = collections.deque()
        self._test_log = test_log
        self._pending_bytes = b''
        self._socket = None
        self._state_machine = None

    def connect(self, host, port):
        s = None
        exc = None
        for resolved in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, _, sa = resolved
            try:
                s = socket.socket(af, socktype, proto)
            except OSError as e:
                s = None
                exc = e
                continue
            try:
                s.settimeout(TIMEOUT)
                s.connect(sa)
                break
            except OSError as e:
                s.close()
                s = None
                exc = e
                continue

        if s is None:
            if exc is None:
                raise socket.error(f"Unable to resolve {host}{port}")
            raise exc

        self._state_machine = UpstreamStateMachine(self._test_log)
        self._socket = s

    def send_msg(self, msg):
        self._state_machine.on_send_tag(msg.tag)
        return self._socket.send(msg.to_bytes())

    def send_tag_and_bytes(self, tag, msg_bytes):
        self._state_machine.on_send_tag(tag)
        return self._socket.send(msg_bytes)

    def __get_next_message(self):
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
                self._state_machine.on_recv(msg)
                self._deque.append(msg)

            if len(self._deque):
                return True

    def expect_message(self, tag, timeout_secs = 60.0):
        first_get = None

        while True:
            while len(self._deque):
                msg = self._deque.popleft()
                if msg.tag == tag:
                    return msg

            first_get = datetime.now()
        
            #queue is exhausted, so now wait for new messages:
            try:
                has_received = self.__get_next_message()
                print(".", end = "")
                if not has_received:
                    raise IOError("socket closed")

            except socket.timeout:
                now = datetime.now()
                delta = now - first_get
                if delta.total_seconds() > timeout_secs:
                    raise

    def close(self):
        if self._socket is not None:
            self._socket.close()
