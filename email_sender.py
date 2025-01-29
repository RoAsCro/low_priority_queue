import json
import os
import boto3

from dotenv import load_dotenv

load_dotenv()
queue = os.getenv("LOW_PRIORITY_QUEUE")
access_id = os.getenv("AWS_ACCESS_KEY_ID")
access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
email = os.getenv("EMAIL")

sqs = boto3.client("sqs",
                   region_name=aws_region,
                   aws_access_key_id=access_id,
                   aws_secret_access_key=access_key)
ses = boto3.client("ses",
                   region_name=aws_region,
                   aws_access_key_id=access_id,
                   aws_secret_access_key=access_key)


def get_message():
    response = sqs.receive_message(
        QueueUrl=queue,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=20
    )

    if "Messages" not in response:
        return

    message = response["Messages"][0]
    receipt_handle = message["ReceiptHandle"]

    sqs.delete_message(
        QueueUrl=queue,
        ReceiptHandle=receipt_handle
    )
    send_email(message)

def send_email(message):
    print("Sending...")
    message_json = json.loads(message["Body"])
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

if __name__ == "__main__":
    while True:
        get_message();