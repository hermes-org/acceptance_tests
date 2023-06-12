"""Test cases for the upstream connection of an IPC-Hermes-9852 interface.
    
        >>>> Board transport direction >>>>
        ----------+          +----------
           this   |          |  System
           code   | -------> |  under
                  |          |  test
        ----------+          +----------
        thus a downstream connection is used by this test code 
        to receive messages from the system under test.
"""

from callback_tags import CbEvt
from test_cases import hermes_testcase, create_downstream_context
from test_cases import EnvironmentManager, message_validator

from ipc_hermes.messages import Tag, Message, TransferState, NotificationCode, SeverityType
from ipc_hermes.connections import ConnectionLost


@hermes_testcase
def test_start_shutdown_n_times():
    """Test start and shutdown server 10 times. Ignore any ServiceDescription received.
        Warning: this test may take a minute to complete."""
    for _ in range(10):
        with create_downstream_context():
            pass


@hermes_testcase
def test_exchange_service_description_shutdown_n_times():
    """Test connect and disconnect n times.
       Exchange ServiceDescription and shutdown server.
       Warning: this test may take a minute to complete.
    """
    for _ in range(10):
        with create_downstream_context() as ctxt:
            env = EnvironmentManager()
            env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
            ctxt.expect_message(Tag.SERVICE_DESCRIPTION)


@hermes_testcase
def test_start_handshake_shutdown():
    """Test start server, receive ServiceDescription, shutdown."""
    with create_downstream_context() as ctxt:
        env = EnvironmentManager()
        env.run_callback(CbEvt.WAIT_FOR_MSG, tag=Tag.SERVICE_DESCRIPTION)
        msg = ctxt.expect_message(Tag.SERVICE_DESCRIPTION)
        message_validator.validate_service_description(env, msg)


@hermes_testcase
def test_terminate_on_wrong_message_in_not_available_not_ready2():
    """Test that connection is closed and reset when wrong messages are recieved
       in state: NotAvailableNotReady
       each sub-test start with handshake and ends with closing the connection
       RevokeMachineReady, StartTransport & StopTransport are not tested as 
       they should never be sent
    """
    env = EnvironmentManager()
    messages = [env.service_description_message(),
                Message.RevokeBoardAvailable(),
                Message.TransportFinished(TransferState.COMPLETE, "some_guid"),
                ]

    for illegal_msg in messages:
        env.log.debug("Sub-test: %s", illegal_msg.tag)
        with create_downstream_context(handshake=True) as ctxt:
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
