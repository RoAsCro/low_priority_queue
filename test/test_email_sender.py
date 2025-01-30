import threading
import time

import boto3
import pytest

import email_sender

from moto import mock_aws


default_email_method  = email_sender.send_email

message_body = '{"priority": "high", "title": "message title", "message": "this is a message body"}'
received_message = None

def replacement_send(message):
    pass

@mock_aws
def test_get_message():
    sqs = prepare_aws()
    sqs[0].send_message(QueueUrl=sqs[1],
                         DelaySeconds=0,
                         MessageBody=message_body)

    retrieved_message = email_sender.get_from_queue()

    assert retrieved_message is not None

@mock_aws
def test_delete_message():
    sqs = prepare_aws()
    mock_sqs = sqs[0]
    queue = sqs[1]
    mock_sqs.send_message(QueueUrl=queue,
                         DelaySeconds=0,
                         MessageBody=message_body)

    retrieved_message = email_sender.get_from_queue()
    email_sender.delete(retrieved_message)

    assert "Message" not in mock_sqs.receive_message(
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=20
    )

@mock_aws
def test_no_message():
    sqs = prepare_aws()

    retrieved_message = email_sender.get_from_queue()

    assert retrieved_message is None


@mock_aws
def test_run_without_email():
    sqs = prepare_aws()
    mock_sqs = sqs[0]
    queue = sqs[1]
    email_sender.send_email = send_email_stub
    mock_sqs.send_message(QueueUrl=queue,
                        DelaySeconds=0,
                        MessageBody=message_body)
    timer_thread = threading.Thread(target=timer, args=[10]) # Ensure test doesn't run forever if it fails
    timer_thread.start()
    email_sender.run()


    assert (received_message is not None # Message was received
            and "Message" not in mock_sqs.receive_message( # Message was deleted
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=20
    ))

@mock_aws
def prepare_aws():
    mock_sqs = boto3.client("sqs", region_name='us-east-1')
    queue = mock_sqs.create_queue(QueueName="team")['QueueUrl']
    email_sender.sqs = mock_sqs
    email_sender.queue = queue
    return mock_sqs, queue

def timer(seconds):
    time.sleep(seconds)
    email_sender.running = False

def send_email_stub(message):
    global received_message
    received_message = message["Body"]
    email_sender.running = False

@pytest.fixture(autouse=True)
def before_each():
    email_sender.send_email = default_email_method
    global received_message
    received_message = None