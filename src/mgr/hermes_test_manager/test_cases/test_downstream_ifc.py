"""Test cases for the downstream connection of an IPC-Hermes-9852 interface.

    >>>> Board transport direction >>>>
    ----------+          +----------
       System |          |  this
       under  | -------> |  code
       test   |          |
    ----------+          +----------
    thus an upstream connection is used by this test code 
    to send messages to the system under test.
"""
import uuid

from callback_tags import CbEvt
from test_cases import hermes_testcase, create_upstream_context
from test_cases import EnvironmentManager, message_validator

from ipc_hermes.messages import MAX_MESSAGE_SIZE
from ipc_hermes.messages import Message, Tag, TransferState, NotificationCode, SeverityType
from ipc_hermes.connections import ConnectionLost

@hermes_testcase
def test_connect_disconnect_n_times():
    """Test connect and disconnect n times. No ServiceDescription sent."""
    for _ in range(10):
        with create_upstream_context(receive=False):
            pass


@hermes_testcase
def test_connect_service_description_disconnect_n_times():
    """Test connect and disconnect n times. 
       Send ServiceDescription but don't wait for answer before closing connection.
    """
    for _ in range(10):
        with create_upstream_context(receive=False) as ctxt:
            ctxt.send_msg(EnvironmentManager().service_description_message())


@hermes_testcase
def test_connect_handshake_disconnect():
    """Test connect, send ServiceDescription, wait for answer, disconnect."""
    with create_upstream_context() as ctxt:
        env = EnvironmentManager()
        ctxt.send_msg(env.service_description_message())
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
        msg = ctxt.expect_message(Tag.SERVICE_DESCRIPTION)
        message_validator.validate_service_description(env, msg)


@hermes_testcase
def test_connect_2_times():
    """Test that only one conenction will be accepted by the server,
       any further connection attempts are rejected and Notification sent
          * NotificationCode should be 2 (Connection refused)
          * It's recommended that Severity should be 2 (Error)
    """
    env = EnvironmentManager()
    msg = None
    with create_upstream_context(receive=False) as ctxt1:

        with create_upstream_context() as ctxt2:
            msg = ctxt2.expect_message(Tag.NOTIFICATION)
            message_validator.validate_notification(env, msg, NotificationCode.CONNECTION_REFUSED, SeverityType.ERROR)

        # verify that ctxt1 still works
        ctxt1.send_msg(env.service_description_message())


@hermes_testcase
def test_maximum_message_size():
    """Test maximum message size by sending a ServiceDescription message of max size.
       Success requires that the system under test responds with its own ServiceDescription.
       Side effects, this also test ability to handle
          * a message spilt into multiple packets
          * a message with an unknown attribute
    """
    with create_upstream_context() as ctxt:
        env = EnvironmentManager()
        msg = Message.ServiceDescription("DownstreamId", env.lane_id)
        msg_bytes = msg.to_bytes()
        splitat = msg_bytes.find(b"LaneId=")
        dummy_attr = b'HermesAcceptanceTestDummyAttributeId="" '
        msg_bytes = msg_bytes[:splitat] + dummy_attr + msg_bytes[splitat:]
        splitat += len(dummy_attr) - 2
        extend_by = MAX_MESSAGE_SIZE - len(msg_bytes)
        msg_bytes = msg_bytes[:splitat] + extend_by * b"x" + msg_bytes[splitat:]
        ctxt.send_tag_and_bytes(msg.tag, msg_bytes)

        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
        ctxt.expect_message(Tag.SERVICE_DESCRIPTION)


@hermes_testcase
def test_multiple_messages_per_packet():
    """Test sending multiple messages in one packet.
       A ServiceDescription message is inserted between two CheckAlive messages
       Success requires that the system under test responds with its own ServiceDescription.
       (None of the CheckAlive messages should be answered.)
    """
    with create_upstream_context() as ctxt:
        env = EnvironmentManager()
        check_alive = Message.CheckAlive()
        service_description = Message.ServiceDescription("DownstreamId", env.lane_id)
        msg_bytes = check_alive.to_bytes() + service_description.to_bytes() + check_alive.to_bytes()
        ctxt.send_tag_and_bytes(service_description.tag, msg_bytes)

        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
        ctxt.expect_message(Tag.SERVICE_DESCRIPTION)


@hermes_testcase
def xtest_terminate_on_illegal_message():
    """Test that connection is closed and reset when unknown message tags are recieved"""
    with create_upstream_context() as ctxt:
        illegal_msg_bytes = b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsUnknownMessage /></Hermes>"
        ctxt.send_tag_and_bytes(None, illegal_msg_bytes)
        # other end has to close connection so check if socked is dead now,
        # optionally a Notification can be sent before closing
        try:
            ctxt.expect_message(Tag.NOTIFICATION)
            ctxt.close()
            raise ValueError("illegal message erroneously accepted")
        except Exception as exc:
            # part 2: try the same after initial handshake
            ctxt.close()
            with create_upstream_context(handshake=True) as ctxt:
                ctxt.send_tag_and_bytes(None, illegal_msg_bytes)
                # other end has to close connection so check if socked is dead now,
                # optionally a Notification can be sent before closing
                try:
                    ctxt.expect_message(Tag.NOTIFICATION)
                    ctxt.close()
                    raise ValueError("illegal message erroneously accepted after handshake") from exc
                except:
                    pass

@hermes_testcase
def test_terminate_on_wrong_message_in_not_available_not_ready():
    """Test that connection is closed and reset when wrong messages are recieved
       in state: NotAvailableNotReady
       each sub-test start with handshake and ends with closing the connection
       RevokeBoardAvailable & TransportFinished are not tested as they should never be sent
    """
    env = EnvironmentManager()
    messages = [env.service_description_message(),
                Message.RevokeMachineReady(),
                Message.StartTransport("some_guid"),
                Message.StopTransport(TransferState.COMPLETE, str(uuid.uuid4()))
                ]

    for illegal_msg in messages:
        env.log.debug("Sub-test: %s", illegal_msg.tag)
        with create_upstream_context(handshake=True) as ctxt:
            ctxt.send_msg(illegal_msg)
            # now we expect a notification
            # callback has no purpose here, TestDriver responeds automatically
            notification = ctxt.expect_message(Tag.NOTIFICATION)
            message_validator.validate_notification(env, notification, NotificationCode.PROTOCOL_ERROR, SeverityType.FATAL)

            # other end has to close connection so check if socked is dead now
            try:
                ctxt.send_msg(Message.Notification(NotificationCode.MACHINE_SHUTDOWN,
                                                   SeverityType.INFORMATION,
                                                   "this should fail"))
                assert False, f"Upstream did not close connection as expected after: {illegal_msg.tag}"
            except ConnectionLost:
                pass

        env.log.info("Passed sub-test: %s", illegal_msg.tag)
