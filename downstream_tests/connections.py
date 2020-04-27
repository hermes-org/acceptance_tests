import collections
from datetime import datetime
import socket
import xml.etree.ElementTree as ET

from messages import Message

TIMEOUT = 1.0
BUFFERSIZE = 4096
ENDTAG = b"</Hermes>"

class UpstreamConnection:

    def __init__(self):
        self._messages = []
        self._socket = None
        

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

        self._deque = collections.deque()
        self._bytes = b''
        self._socket = s

    def send(self, data):
        return self._socket.send(data)

    def __get_next_message(self):
        while True:
            received = self._socket.recv(BUFFERSIZE)
            if not received:
                return False
            self._bytes += received

            while True:
                index = self._bytes.find(ENDTAG)
                if index == -1:
                    break
                splitat = index + len(ENDTAG)
                msg, self._bytes = self._bytes[:splitat], self._bytes[splitat:0]
                root = ET.fromstring(msg)
                self._deque.append(Message(root))

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
