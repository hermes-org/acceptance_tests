from datetime import datetime
import sys
from messages import Message
from contextlib import contextmanager

from connections import UpstreamConnection
from test_log import create_log, TestLog

MAXMESSAGE = 65536
TEST_CASES = []
globalHost='127.0.0.1'
globalPort=50101
testFailed=False

@contextmanager
def create_upstream_context(host= globalHost, port = globalPort):
    uc = UpstreamConnection()
    try:
        uc.connect(host, port)
        yield uc
        uc.close()
    except:
        uc.close()
        raise

@contextmanager
def create_upstream_context_with_hand_shake(host = "localhost", port = 50101):
    uc = UpstreamConnection()
    try:
        uc.connect(host, port)
        uc.send(Message.ServiceDescription("AcceptanceTest", 2).to_bytes())
        uc.expect_message("ServiceDescription")
        yield uc
        uc.close()
    except:
        uc.close()
        raise
    
def test_decorator(func):
    global testFailed;
    def test_wrapper(mode, count):
        if (mode==1):
            print(f"{count} - {func.__name__}")
        else:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%M')
            print(f"{timestamp} Executing {func.__name__}...", end = "")
            try:
                func()
            except Exception as e:
                testFailed=True
                print(f"FAILED with error: {str(e)}")
            else:
                print(f"succeeded")

    TEST_CASES.append(test_wrapper)
        
    return test_wrapper

################################################################################################
# start with test cases here

@test_decorator
def connect_disconnect_n_times():
    for _ in range(10):
        with create_upstream_context() as ctxt:
            pass

@test_decorator
def connect_2_times():
    uc1 = UpstreamConnection()
    try:
        uc1.connect(globalHost, globalPort)
    except:
        uc1.close()
        raise

    uc2 = UpstreamConnection()
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
#    len1=uc1.send(Message.ServiceDescription("AcceptanceTest1", 2).to_bytes())
#    len2=uc2.send(Message.ServiceDescription("AcceptanceTest2", 2).to_bytes())
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
            ctxt.send(Message.ServiceDescription("AcceptanceTest", 2).to_bytes())

@test_decorator
def connect_handshake_disconnect():
    with create_upstream_context_with_hand_shake() as ctxt:
        pass

@test_decorator
def test_maximum_message_size():
    with create_upstream_context() as ctxt:
        msg = Message.ServiceDescription("DownstreamId", 1).to_bytes()
        splitat = msg.find(b"LaneId=")
        dummy_attr = b'HermesAcceptanceTestDummyAttributeId="" '
        msg = msg[:splitat] + dummy_attr + msg[splitat:]
        splitat += len(dummy_attr) - 2
        extend_by = MAXMESSAGE - len(msg)
        msg = msg[:splitat] + extend_by * b"x" + msg[splitat:]
        ctxt.send(msg)
        ctxt.expect_message("ServiceDescription")

@test_decorator
def test_multiple_messages_per_packet():
    with create_upstream_context() as ctxt:
        msg = Message.CheckAlive().to_bytes()
        msg = msg + Message.ServiceDescription("DownstreamId", 1).to_bytes()
        msg = msg + Message.CheckAlive().to_bytes()
        ctxt.send(msg)
        ctxt.expect_message("ServiceDescription")        


@test_decorator
def test_wrong_messages():
    with create_upstream_context() as ctxt:
        # this test can send loads of messages and combinations which are not expected or not valid in current context
        # todo: write ech step to log to easily find the position where something went wrong

        msg=b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsNotAKnownMessage /></Hermes>"
        ctxt.send(msg)
        ctxt.expect_message("Notification")        

        msg = Message.RevokeBoardAvailable().to_bytes()
        ctxt.send(msg)
        ctxt.expect_message("Notification")        
        
        msg = Message.RevokeMachineReady().to_bytes()
        ctxt.send(msg)
        ctxt.expect_message("Notification")        


def main():
    global g_log

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
              for test_case in TEST_CASES:
                 test_case(0,0)
              working=False
           else:
              if (selection<=len(TEST_CASES)):
                 TEST_CASES[selection-1](0,0)
                 working=False

    if (testFailed==True):
        print("Test run FAILED!")

if __name__ == '__main__':
    main()

