from datetime import datetime
from messages import Message, TransferState
from contextlib import contextmanager

from connections import UpstreamConnection
from test_log import create_log, print_and_log, TestResult

#set the real IP and port number of your device here
globalHost='127.0.0.1'
globalPort=50101

MAXMESSAGE = 65536
TEST_CASES = []
test_failed = False
log=0

@contextmanager
def create_upstream_context(host=globalHost, port = globalPort):
    uc = UpstreamConnection(log)
    try:
        uc.connect(host, port)
        yield uc
        uc.close()
    except:
        uc.close()
        raise

@contextmanager
def create_upstream_context_with_handshake(host = "localhost", port = 50101):
    uc = UpstreamConnection(log)
    try:
        uc.connect(host, port)
        uc.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        uc.expect_message("ServiceDescription")
        yield uc
        uc.close()
    except:
        uc.close()
        raise
    
def test_decorator(func):
    def test_wrapper(mode, count):
        global test_failed
        if (mode==1):
            print(f"{count} - {func.__name__}")
        else:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%M')
            print(f"{timestamp} Executing {func.__name__}...", end="")
            log.log_start(f"{count} - {func.__name__}")
            try:
                func()
            except Exception as e:
                test_failed = True
                print(f"FAILED with error: {str(e)}")
                log.log_finish(f"{count} - {func.__name__}", TestResult.FAIL)
            else:
                print("succeeded")
                log.log_finish(f"{count} - {func.__name__}", TestResult.PASS)

    TEST_CASES.append(test_wrapper)
        
    return test_wrapper

################################################################################################
# start with test cases here

@test_decorator
def connect_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context():
            pass

@test_decorator
def connect_2_times():
    uc1 = UpstreamConnection(log)
    try:
        uc1.connect(globalHost, globalPort)
    except:
        uc1.close()
        raise

    uc2 = UpstreamConnection(log)
    try:
        uc2.connect(global_host, global_port)
    except:
        uc1.close()
        uc2.close()
        return

    uc1.close()
    uc2.close()
    raise ValueError("second connection was accepted")

#
#    len1=uc1.send_msg(Message.ServiceDescription("AcceptanceTest1", 2))
#    len2=uc2.send_msg(Message.ServiceDescription("AcceptanceTest2", 2))
#    if ((len1>0) or (len2>0)):
#        try:
#            uc2.expect_message("ServiceDescription")
#        except:
#            uc1.close()
#            uc2.close()
#            return
#        uc1.close()
#        uc2.close()
#        raise ValueError("second connection was accepted")
#    else:
#        uc1.close()
#        uc2.close()


@test_decorator
def connect_service_description_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context() as ctxt:
            ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))

@test_decorator
def connect_handshake_disconnect():
    with create_upstream_context_with_handshake():
        pass

@test_decorator
def test_maximum_message_size():
    with create_upstream_context() as ctxt:
        msg = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = msg.to_bytes()
        splitat = msg_bytes.find(b"LaneId=")
        dummy_attr = b'HermesAcceptanceTestDummyAttributeId="" '
        msg_bytes = msg_bytes[:splitat] + dummy_attr + msg_bytes[splitat:]
        splitat += len(dummy_attr) - 2
        extend_by = MAXMESSAGE - len(msg_bytes)
        msg_bytes = msg_bytes[:splitat] + extend_by * b"x" + msg_bytes[splitat:]
        ctxt.send_tag_and_bytes(msg.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")

@test_decorator
def test_multiple_messages_per_packet():
    with create_upstream_context() as ctxt:
        check_alive = Message.CheckAlive()
        service_description = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = check_alive.to_bytes() + service_description.to_bytes() + check_alive.to_bytes()
        ctxt.send_tag_and_bytes(service_description.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")

@test_decorator
def test_terminate_on_illegal_message():
    with create_upstream_context() as ctxt:
        msg_bytes = b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsNotAKnownMessage /></Hermes>"
        ctxt.send_tag_and_bytes(None, msg_bytes)
        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
        try:
            ctxt._socket.recv(0)
            uc.expect_message("Notification")
            ctxt.close()
            raise ValueError("illegal message erroneously accepted")
        except:
            # try the same after initial handshake
            ctxt.close()
            with create_upstream_context() as ctxt:
                ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
                ctxt.expect_message("ServiceDescription")

                ctxt.send_tag_and_bytes(None, msg_bytes)
                # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
                try:
                    ctxt._socket.recv(0)
                    uc.expect_message("Notification")
                    ctxt.close()
                    raise ValueError("illegal message erroneously accepted after handshake")
                except:
                    pass

@test_decorator
def test_terminate_on_msg_before_service_desc():
    with create_upstream_context() as ctxt:
        msg = Message.RevokeBoardAvailable()
        ctxt.send_msg(msg)
        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
        try:
            ctxt._socket.recv(0)
            uc.expect_message("Notification")
            ctxt.close()
            raise ValueError("RevokeBoardAvailable erroneously accepted")
        except:
            # try with the next message
            ctxt.close()

            with create_upstream_context() as ctxt:
                msg = Message.BoardAvailable("TestBoard","HermesAcceptanceTester")
                board_id = msg.data.get("BoardId")
                ctxt.send_msg(msg)
                # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
                try:
                    ctxt._socket.recv(0)
                    uc.expect_message("Notification")
                    ctxt.close()
                    raise ValueError("BoardAvailable erroneously accepted")
                except:
                    # try with the next message
                    ctxt.close()

                    with create_upstream_context() as ctxt:
                        msg = Message.TransportFinished(TransferState.COMPLETE, board_id)
                        ctxt.send_msg(msg)
                        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
                        try:
                            ctxt._socket.recv(0)
                            uc.expect_message("Notification")
                            ctxt.close()
                            raise ValueError("TransportFinished erroneously accepted")
                        except:
                            # try with the next message
                            ctxt.close()

                            with create_upstream_context() as ctxt:
                                msg = Message.BoardForecast()
                                ctxt.send_msg(msg)
                                # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
                                try:
                                    ctxt._socket.recv(0)
                                    uc.expect_message("Notification")
                                    ctxt.close()
                                    raise ValueError("TransportFinished erroneously accepted")
                                except:
                                    # try with the next message
                                    ctxt.close()

        
@test_decorator
def test_terminate_on_unexpected_revoke_board_available():
    with create_upstream_context() as ctxt:
        ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        ctxt.expect_message("ServiceDescription")

        msg = Message.RevokeBoardAvailable()
        ctxt.send_msg(msg)
        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
        try:
            ctxt._socket.recv(0)
            uc.expect_message("Notification")
            ctxt.close()
            raise ValueError("RevokeBoardAvailable erroneously accepted after handshake")
        except:
            pass

        
@test_decorator
def test_terminate_on_unexpected_revoke_machine_ready():
    with create_upstream_context() as ctxt:
        ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        ctxt.expect_message("ServiceDescription")

        msg = Message.RevokeMachineReady()
        ctxt.send_msg(msg)
        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
        try:
            ctxt._socket.recv(0)
            uc.expect_message("Notification")
            ctxt.close()
            raise ValueError("RevokeMachineReady erroneously accepted after handshake")
        except:
            pass

@test_decorator
def test_terminate_on_unexpected_transport_finished():
    with create_upstream_context() as ctxt:
        ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
        ctxt.expect_message("ServiceDescription")

        msg = Message.TransportFinished(TransferState.COMPLETE, "some_guid")
        ctxt.send_msg(msg)
        # other end has to close connection so check if socked is dead now, optionally a Notification can be sent before closing
        try:
            ctxt._socket.recv(0)
            uc.expect_message("Notification")
            ctxt.close()
            raise ValueError("TransportFinished erroneously accepted after handshake")
        except:
            pass

@test_decorator
def test_complete_cycle():
    with create_upstream_context() as ctxt:
        ctxt.send_msg(Message.ServiceDescription("AcceptanceTestCompleteCycle", 2))
        ctxt.expect_message("ServiceDescription")

        msg = Message.MachineReady()
        ctxt.send_msg(msg)
        board_available = ctxt.expect_message("BoardAvailable")
        board_id = board_available.data.get("BoardId")

        msg = Message.StartTransport(board_id)
        ctxt.send_msg(msg)
        ctxt.expect_message("TransportFinished")

        msg = Message.StopTransport(TransferState.COMPLETE, board_id)
        ctxt.send_msg(msg)
        ctxt.close();


def main():
    global log
    with create_log("AutomaticDownstream") as log:
        working=True
        while (working):
            i=1
            print("0 - all tests")
            for test_case in TEST_CASES:
                test_case(1,i) # print testcase names only
                i=i+1

            selection=int(input())
            if (selection==0):
                i=0;
                for test_case in TEST_CASES:
                    i=i+1
                    test_case(0,i)
                working=False
            else:
                if (selection<=len(TEST_CASES)):
                    TEST_CASES[selection-1](0,selection)
                working=False

        if test_failed == True:
            print_and_log("Test run FAILED!", log)
            return 1

    return 0

if __name__ == '__main__':
    main()

