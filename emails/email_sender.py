import json
import os
from venv import logger

import boto3

from botocore import exceptions
from dotenv import load_dotenv
from flask import Flask

import abstract_comsumer

consumer = abstract_comsumer
load_dotenv()


email = os.getenv("EMAIL")
aws_region = os.getenv("AWS_REGION")
ses = None
exception = exceptions.ClientError
def send(message_to_send):
    global ses
    if ses is None:
        ses = boto3.client("ses",
                     region_name=aws_region,
                     aws_access_key_id=consumer.access_id,
                     aws_secret_access_key=consumer.access_key)
    message_json = json.loads(message_to_send["Body"])
    priority = message_json['priority'].capitalize()
    ses.send_email(Source=email,
                   Destination={"ToAddresses": [email]},
                   Message={"Subject":
                                {"Data": f"{priority} priority - {message_json['title']}"},
                            "Body":
                                {"Text":
                                     {"Data": f"{message_json['message']}\n"
                                              f"(Message sent automatically via bug queue)"}
                                 }
                            })


consumer.send = send
consumer.exception = exception
bg_thread = consumer.background_thread()
def run():
    health_checker = Flask(__name__)
    health_checker.register_blueprint(consumer.router)
    return health_checker

if __name__ == "__main__":
    try:
        run().run(host="0.0.0.0")
    except KeyboardInterrupt:
        logger.info("Shutting Down...")
        bg_thread.join()
        consumer.running = False