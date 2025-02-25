import threading
import time

import boto3
import botocore
import pytest
from moto.batch import batch_backends
from moto.ses.models import SESBackend

from emails.email_sender import EmailConsumer

from moto import mock_aws
from moto.core import DEFAULT_ACCOUNT_ID
from moto.ses import ses_backends
# if 'us-east-1' in batch_backends:
#     batch_backend = batch_backends['us-east-1']
class ConsumerStub(EmailConsumer):
    sent_message = None

    @mock_aws()
    def __init__(self):
        super().__init__()
        self.email = "test@nowhere.com"
        self.old_send = self.send
        self.send = self.send_stub

    def send_stub(self, message):
        self.old_send(message)
        self.sent_message = ses_backends[DEFAULT_ACCOUNT_ID]["us-east-1"].sent_messages[0]

consumer = ConsumerStub()

message_body = '{"priority": "high", "title": "message title", "message": "this is a message body"}'

@mock_aws
def test_get_message():
    sqs = prepare_aws()
    sqs[0].send_message(QueueUrl=sqs[1],
                         DelaySeconds=0,
                         MessageBody=message_body)

    retrieved_message = consumer.get_from_queue()

    assert retrieved_message is not None

@mock_aws
def test_delete_message():
    sqs = prepare_aws()
    mock_sqs = sqs[0]
    queue = sqs[1]
    mock_sqs.send_message(QueueUrl=queue,
                         DelaySeconds=0,
                         MessageBody=message_body)

    retrieved_message = consumer.get_from_queue()
    consumer.delete(retrieved_message)

    assert "Message" not in mock_sqs.receive_message(
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

@mock_aws
def test_no_message():
    prepare_aws()

    retrieved_message = consumer.get_from_queue()

    assert retrieved_message is None


@mock_aws
def test_process():
    sqs = prepare_aws()
    mock_sqs = sqs[0]
    queue = sqs[1]
    mock_sqs.send_message(QueueUrl=queue,
                        DelaySeconds=0,
                        MessageBody=message_body)
    timer_thread = threading.Thread(target=timer, args=[20]) # Ensure test doesn't run forever if it fails
    timer_thread.start()
    consumer.running = True
    consumer.process()
    consumer.running = False
    assert (consumer.sent_message is not None  # Message was received
            and ("high" and "message title") in consumer.sent_message.subject
            and "this is a message body" in consumer.sent_message.body
            and "Message" not in mock_sqs.receive_message( # Message was deleted
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    ))

@mock_aws
def prepare_aws():
    mock_sqs = boto3.client("sqs", region_name='us-east-1')
    queue = mock_sqs.create_queue(QueueName="team")['QueueUrl']
    consumer.sqs = mock_sqs
    consumer.queue = queue
    consumer.ses = boto3.client("ses",
                         region_name="us-east-1")
    consumer.ses.verify_email_identity(EmailAddress="test@nowhere.com")
    return mock_sqs, queue

def timer(seconds):
    time.sleep(seconds)
    consumer.running = False

@pytest.fixture(autouse=True)
def before_each():
    consumer.sent_message = None
