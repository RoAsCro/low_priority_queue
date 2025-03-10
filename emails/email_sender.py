import json
import logging
import os

import boto3
from botocore import exceptions
from dotenv import load_dotenv
from sqs_consumer.abstract_consumer import AbstractConsumer

load_dotenv()
exception = exceptions.ClientError
class EmailConsumer(AbstractConsumer):
    def __init__(self):
        super().__init__()
        self.exception = IndexError
        self.email = os.getenv("EMAIL")
        self.ses = None



    def send(self, message_to_send):
        if self.ses is None:
            self.ses = boto3.client("ses",
                         region_name=self.aws_region,
                         aws_access_key_id=consumer.access_id,
                         aws_secret_access_key=consumer.access_key)
        message_json = json.loads(message_to_send["Body"])
        priority = message_json['priority'].capitalize()

        self.ses.send_email(Source=self.email,
                       Destination={"ToAddresses": [self.email]},
                       Message={"Subject":
                                    {"Data": f"{priority} priority - {message_json['title']}"},
                                "Body":
                                    {"Text":
                                         {"Data": f"{message_json['message']}\n"
                                                  f"(Message sent automatically via bug queue)"}
                                     }
                                })


consumer = EmailConsumer()
run = consumer.run

if __name__ == "__main__":
    try:
        run().run(host="0.0.0.0")
    except KeyboardInterrupt:
        consumer.info_logger.info("Shutting Down...")
        consumer.bg_thread.join()
        consumer.running = False