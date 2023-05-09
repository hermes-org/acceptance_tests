"""Test cases for the downstream connection of an IPC-Hermes-9852 interface.

    >>>> Board transport direction >>>>
    ----------+          +----------
       System |          |  this
       under  | -------- |  code
       test   |          |
    ----------+          +----------
    thus an upstream connection is used by this test code 
    to send messages to the system under test.

    The test code does not know which lane interface is used,
    this is controlled by host/port configuration.
"""
import pytest

from test_cases import hermes_testcase, get_log, EnvironmentManager
from test_cases import create_upstream_context, create_upstream_context_with_handshake


from ipc_hermes.messages import Message, Tag, MAX_MESSAGE_SIZE

@hermes_testcase
def test_connect_disconnect_n_times():
    """Test connect and disconnect n times. No ServiceDescription sent."""
    for _ in range(10):
        with create_upstream_context():
            pass


@hermes_testcase
def test_connect_service_description_disconnect_n_times():
    """Test connect and disconnect n times. 
       Send ServiceDescription but don't wait for answer before closing connection.
    """
    for _ in range(10):
        with create_upstream_context() as ctxt:
            ctxt.send_msg(EnvironmentManager().service_description_message())


@hermes_testcase
@pytest.mark.testdriver
def test_connect_handshake_disconnect():
    """Test connect, send ServiceDescription, wait for answer, disconnect."""
    with create_upstream_context() as ctxt:
        env = EnvironmentManager()
        ctxt.send_msg(env.service_description_message())
        if env.include_handshake:
            env.run_callback(__name__, 'Action required: Send ServiceDescription')

        msg = ctxt.expect_message(Tag.SERVICE_DESCRIPTION)
        assert msg.data.get('LaneId') == env.lane_id


@hermes_testcase
def test_connect_2_times():
    """Test to connect twice. Second connection should be rejected and notification sent."""
    msg = None
    with create_upstream_context() as ctxt1:

        with create_upstream_context() as ctxt2:
            msg = ctxt2.expect_message(Tag.NOTIFICATION)

        # verify that ctxt1 still works
        ctxt1.send_msg(EnvironmentManager().service_description_message())

    assert msg.data.get('NotificationCode') == '2'
    # TODO: recommended warning level?
    if msg.data.get('Severity') != '2':
        get_log().warning('%s: Notification was sent but Severity is not 2 (Error), recieved %s',
                          'test_connect_2_times', msg.data.get('Severity'))


@hermes_testcase
def test_maximum_message_size():
    """Test maximum message size by sending a ServiceDescription message of max size.
       Success requires that the system under test responds with its own ServiceDescription.
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

        if env.include_handshake:
            env.run_callback(__name__, 'Action required: Send ServiceDescription')
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

        if env.include_handshake:
            env.run_callback(__name__, 'Action required: Send ServiceDescription')
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
            ctxt.receive_data()
            ctxt.expect_message(Tag.NOTIFICATION)
            ctxt.close()
            raise ValueError("illegal message erroneously accepted")
        except Exception as exc:
            # part 2: try the same after initial handshake
            ctxt.close()
            with create_upstream_context_with_handshake() as ctxt:
                ctxt.send_tag_and_bytes(None, illegal_msg_bytes)
                # other end has to close connection so check if socked is dead now,
                # optionally a Notification can be sent before closing
                try:
                    ctxt.receive_data()
                    ctxt.expect_message(Tag.NOTIFICATION)
                    ctxt.close()
                    raise ValueError("illegal message erroneously accepted after handshake") from exc
                except:
                    pass
