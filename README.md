# Webhook to SQS #
This code implements a simple webhook for a Github repository in
Python. We process the events as they come in from Github and enqueue
them into an AWS SQS fifo queue for further processing.

## Development Environment ##
You'll need to make sure you have `python 3.6` and `pipenv` installed.

## Install Patched Zappa Library ## You need to use this patched
version of Zappa until the patch is merged into the next Zappa
release. Zappa issue #1188 prevents forwarding of events if the header
is spelled "content-type" instead of "Content-Type".

``
pipenv install -e \
git+https://github.com/lispmeister/Zappa.git#egg=private
``

## Create an IAM Role ##
Go to the AWS console and create a separate IAM role under your AWS
account for your lambda experiments.
Go to the permissions pane for the user and grant the following
permissions via an AWS managed policy:
- AWSLambdaFullAccess
- AmazonS3FullAccess
- AmazonSQSFullAccess

## Add Keys ##
Add the keys for the role to your credentials file in `$HOME/.aws/credentials`.
Example entry:

    [lambda] # using the keypair for the Lambda-user
    access_key_id = <key id>
    aws_secret_access_key = <secret access key>
    aws_access_key_id = <access key id>

## Configure an SQS Queue ##
We want to create a FIFO queue via AWS SQS. Let's get a skeleton for
the provisioning query first:
``
aws --profile 'lambda' sqs create-queue \
--generate-cli-skeleton
``

Result:
``
{
    "QueueName": "",
    "Attributes": {
        "KeyName": ""
    }
}
``
We create the file ``webhook-sqs-config.json`` with the following
content:
``
{
 "VisibilityTimeout": "60",
 "MaximumMessageSize": "262144",
 "MessageRetentionPeriod": "600",
 "DelaySeconds": "0",
 "ReceiveMessageWaitTimeSeconds": "0",
 "FifoQueue": "true",
 "ContentBasedDeduplication": "true"
}
``


Now create the queue:
``
aws --profile 'lambda' sqs create-queue \
--queue-name 'webhook.fifo' \
--attributes file://webhook-sqs-config.json
``

Result:
``
{
    "QueueUrl": "https://queue.amazonaws.com/042837844403/webhook.fifo"
}
``

Get the queue URL:
``
aws --profile 'lambda' sqs get-queue-url \
--queue-name 'webhook.fifo'
``

Result:
``
{
    "QueueUrl": "https://queue.amazonaws.com/042837844403/webhook.fifo"
}
``

We will use the queue URL in our Python code.

# Local Testing with Ngrok #
## Install Ngrok ##
Download and install into $HOME/bin or /usr/local/bin.
<https://ngrok.com/download>

## Start Ngrok ##
Start the ngrok daemon and note down the URL:

    ngrok http 5000

Output

    Session Status                online
    Session Expires               7 hours, 59 minutes
    Version                       2.2.8
    Region                        United States (us)
    Web Interface                 http://127.0.0.1:4040
    Forwarding                    http://5318c304.ngrok.io -> localhost:5000
    Forwarding                    https://5318c304.ngrok.io -> localhost:5000

## Configure the Webhook ##
You'll need to copy the forwarding URL into the payload URL field for
the webhook of your Github repository. See the following web page for
instructions:
<https://developer.github.com/webhooks/configuring/>

Your payload URL should look something like this:
https://5318c304.ngrok.io/postreceive

Your webhook is configured at the path `postreceive` awaiting data.

## Start the Webhook ##
Change into the `webhook_to_sqs` directory and issue the following
commands:

    pipenv install
    pipenv shell
    export FLASK_APP=webhook_to_sqs.py
    export FLASK_DEBUG=1
    flask run --host=0.0.0.0

## Test the Webhook ##
### Push ###
Checkout your Github project, modify a file, commit the file, push
the changes to Github. You should see some console output stating

    Received push event.
    Enqueued to SQS.

### Create Issue ###
Open the issues page for your git repository on Github and create an
issue. Once the issue is created your webhook will be called and you
should see some output on the console where you started the webhook on
your local machine.

    Received issues event.
    Enqueued to SQS.

### Create a Issue Comment ###
Open the issues page for your git repository on Github and comment on
the issue you just created. Your webhook will be called and you
should see some output on the console where you started the webhook on
your local machine.

    Received issue_comment event.
    Enqueued to SQS.

# Deploying to AWS Lambda #
## Configure Zappa ##
Change into the `simple_webhook` directory and issue the following
commands:

    pipenv install
    pipenv shell
    zappa init

Make sure you specify your IAM role during the init process. Choose
`us-east-1` as the default region. Zappa will generate the S3 bucket
name for you and will also create the bucket at first deployment.
After initialization your `zappa_settings.json` file should look
similar to this:

    {
        "dev": {
            "app_function": "webhook_to_sqs.app",
            "aws_region": "us-east-1",
            "profile_name": "lambda",
            "project_name": "webhook_to_sqs",
            "runtime": "python3.6",
            "s3_bucket": "zappa-pxizg6md21"
        }
    }

## Start Lambda Service ##
Deploy the webhook service like this:

    zappa deploy dev

After the deploy (which creates the S3 bucket to store the code when
you run it for the first time) Zappa will show the URL for the
service in the last line of the output:

    Deployment complete!: https://m8auwlqzm4.execute-api.us-east-1.amazonaws.com/dev


## Configure the Webhook ##
You'll need to copy the lambda endpoint URL into the payload URL field for
the webhook of your Github repository. See the following web page for
instructions:
<https://developer.github.com/webhooks/configuring/>

For AWS lambda your payload URL should look something like this:
<https://m8auwlqzm4.execute-api.us-east-1.amazonaws.com/dev/postreceive>

Your webhook is configured at the path `postreceive` awaiting data.

## Zappa Tracing ##
You can display a trace of the service calls like this:

    zappa tail

## Test the Webhook ##

## Test the Webhook ##
### Push ###
Checkout your Github project, modify a file, commit the file, push
the changes to Github. You should see some console output stating

    Received push event.
    Enqueued to SQS.

### Create Issue ###
Open the issues page for your git repository on Github and create an
issue. Once the issue is created your webhook will be called and you
should see some output on the console where you started the webhook on
your local machine.

    Received issues event.
    Enqueued to SQS.

### Create a Issue Comment ###
Open the issues page for your git repository on Github and comment on
the issue you just created. Your webhook will be called and you
should see some output on the console where you started the webhook on
your local machine.

    Received issue_comment event.
    Enqueued to SQS.
