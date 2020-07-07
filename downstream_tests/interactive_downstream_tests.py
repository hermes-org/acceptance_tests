from datetime import datetime
from messages import Message, MAXMESSAGESIZE, TransferState
from contextlib import contextmanager

from connections import UpstreamConnection
from test_log import create_log, print_and_log, TestResult

#set the real IP and port number of your device here
globalHost='127.0.0.1'
globalPort=50101

@contextmanager
def create_upstream_context(host=globalHost, port = globalPort):
    uc = UpstreamConnection(TestDecorator.log)
    try:
        uc.connect(host, port)
        yield uc
        uc.close()
    except:
        uc.close()
        raise

@contextmanager
def create_upstream_context_with_handshake( host = "localhost", port = 50101):
    uc = UpstreamConnection(TestDecorator.log)
    try:
        uc.connect(host, port)
        uc.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        uc.expect_message("ServiceDescription")
        yield uc
        uc.close()
    except:
        uc.close()
        raise

@contextmanager
def create_upstream_context_with_board_available( host = "localhost", port = 50101):
    uc = UpstreamConnection(TestDecorator.log)
    try:
        uc.connect(host, port)
        uc.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        uc.expect_message("ServiceDescription")
        uc.expect_message("BoardAvailable")
        yield uc
        uc.close()
    except:
        uc.close()
        raise
    
class TestDecorator:

    test_cases = []
    test_failed = False
    log = None

    def __init__(self, func):
        def test_wrapper(mode, count):
            if mode == 1:
                print(f"{count} - {func.__name__}")
                return

            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%M')
            print(f"{timestamp} Executing {func.__name__}...", end="")
            type(self).log.log_start(func.__name__)
            try:
                func()
            except Exception as e:
                type(self).test_failed = True
                print(f"FAILED with error: {e}")
                type(self).log.log_finish(func.__name__, TestResult.FAIL)
            else:
                print("succeeded")
                type(self).log.log_finish(func.__name__, TestResult.PASS)

        type(self).test_cases.append(test_wrapper)
        self._func = test_wrapper

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

################################################################################################
# start with test cases here

@TestDecorator
def connect_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context():
            pass

@TestDecorator
def connect_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context():
            pass

@TestDecorator
def connect_board_available_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context_with_board_available() as ctxt:
            ctxt.send_msg(Message.MachineReady())
            ctxt.send_msg(Message.RevokeMachineReady())

@TestDecorator
def connect_and_transfer():
    with create_upstream_context_with_handshake() as ctxt:
        ctxt.send_msg(Message.MachineReady())
        board_available = ctxt.expect_message("BoardAvailable")
        board_id = board_available.data.get("BoardId")
        ctxt.send_msg(Message.StartTransport(board_id))
        ctxt.send_msg(Message.StopTransport(TransferState.COMPLETE, board_id))
        transport_finished = ctxt.expect_message("TransportFinished")
        assert transport_finished.data.get("BoardId") == board_id, "BoardId mismatch"

@TestDecorator
def test_maximum_message_size():
    with create_upstream_context() as ctxt:
        msg = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = msg.to_bytes()
        splitat = msg_bytes.find(b"LaneId=")
        dummy_attr = b'HermesAcceptanceTestDummyAttributeId="" '
        msg_bytes = msg_bytes[:splitat] + dummy_attr + msg_bytes[splitat:]
        splitat += len(dummy_attr) - 2
        extend_by = MAXMESSAGESIZE - len(msg_bytes)
        msg_bytes = msg_bytes[:splitat] + extend_by * b"x" + msg_bytes[splitat:]
        ctxt.send_tag_and_bytes(msg.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")

@TestDecorator
def test_multiple_messages_per_packet():
    with create_upstream_context() as ctxt:
        check_alive = Message.CheckAlive()
        service_description = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = check_alive.to_bytes() + service_description.to_bytes() + check_alive.to_bytes()
        ctxt.send_tag_and_bytes(service_description.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")

def main():
    with create_log("AutomaticDownstream") as log:
        TestDecorator.log = log
        working=True
        while (working):
            i=1
            print("0 - all tests")
            for test_case in TestDecorator.test_cases:
                test_case(1,i) # print testcase names only
                i=i+1

            selection=int(input())
            if (selection==0):
                for test_case in TestDecorator.test_cases:
                    test_case(0,0)
                working=False
            else:
                if (selection<=len(TestDecorator.test_cases)):
                    TestDecorator.test_cases[selection-1](0,0)
                working=False

        if TestDecorator.test_failed:
            print_and_log("Test run FAILED!", log)
            return 1

    return 0

if __name__ == '__main__':
    main()


