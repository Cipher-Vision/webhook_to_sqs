from github_webhook import Webhook
from flask import Flask
import logging
import boto3
import datetime

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

app = Flask(__name__)   # Standard Flask app
webhook = Webhook(app)  # Defines '/postreceive' endpoint

# Create SQS client
sqs = boto3.client('sqs')
queue_url = 'https://queue.amazonaws.com/042837844403/webhook.fifo'


# Create message attributes JSON
def set_message_attributes(source, timestamp, event_type):
    attributes = {
        'Source': {
            'DataType': 'String',
            'StringValue': source
        },
        'Timestamp': {
            'DataType': 'String',
            'StringValue': timestamp
        },
        'EventType': {
            'DataType': 'String',
            'StringValue': event_type
        }
    }
    return attributes


# Send message to SQS queue
def send_to_sqs(attributes, message):
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes=attributes,
        MessageBody=message)
    logging.debug("Event enqueued to SQS: %s", response['MessageId'])


@app.route("/")        # Standard Flask endpoint
def hello_world():
    logging.debug('Hello World!')
    return "Hello, World!"


# Define a handler for the 'push' event
@webhook.hook()
def on_push(data):
    logging.debug("Received push event.")
    timestamp = datetime.datetime.utcnow().isoformat()
    attributes = set_message_attributes('Github repo', timestamp, 'push')
    send_to_sqs(attributes, data)


# Define a handler for the "issues" event
@webhook.hook(event_type='issues')
def on_issues(data):
    logging.debug("Received issues event.")
    timestamp = datetime.datetime.utcnow().isoformat()
    attributes = set_message_attributes('Github repo', timestamp, 'issues')
    send_to_sqs(attributes, data)


# Define a handler for the "issue_comment" event
@webhook.hook(event_type='issue_comment')
def on_issue_comment(data):
    logging.debug("Received issue_comment event.")
    timestamp = datetime.datetime.utcnow().isoformat()
    attributes = set_message_attributes('Github repo', timestamp,
                                        'issue_comment')
    send_to_sqs(attributes, data)


if __name__ == "__main__":
    app.run()
