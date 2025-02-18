import os
import threading
from abc import ABC, abstractmethod
from venv import logger

import boto3
from dotenv import load_dotenv
from flask import Flask, Blueprint

load_dotenv()
# Environment variables
queue = os.getenv("QUEUE")
access_id = os.getenv("AWS_ACCESS_KEY_ID")
access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
exception = Exception
router = Blueprint("messages", __name__, url_prefix="/queue_1")

sqs = boto3.client("sqs",
                   region_name="us-east-1",
                   aws_access_key_id=access_id,
                   aws_secret_access_key=access_key
                   )

running = False


def get_from_queue():

    response = sqs.receive_message(
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=20
    )

    if "Messages" not in response:
        return None

    message = response["Messages"][0]

    return message

def send(message_to_send):
    pass

def delete(message):
    receipt_handle = message["ReceiptHandle"]

    sqs.delete_message(
        QueueUrl=queue,
        ReceiptHandle=receipt_handle
    )

def process():
    global running
    running = True
    while running:
        message = get_from_queue()
        if message:
            try:
                send(message)
            except exception as ex:
                logger.info(ex)
                continue
            delete(message)

def background_thread():
    thread = threading.Thread(target=process, daemon=True)
    thread.start()
    return thread



@router.get("/health")
def health_check():
    return 'Ok', 200

# def run():
#     try:
#         health_checker = Flask(__name__)
#         health_checker.register_blueprint(router)
#         health_checker.run(host="0.0.0.0")
#     except KeyboardInterrupt:
#         logger.info("Shutting Down...")
#         # bg_thread.join()
#         global running
#         running = False



