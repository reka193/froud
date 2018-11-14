import boto3
import sys
from common import load_config_json
from common import write_to_file
from common import init_keys
from common import parsing
from common import bucket_upload


def init():
    #init_keys()
    description = '[*] SQS message scanner.\n' \
                  '[*] Specify the name of the queue to save the messages from.\n' \
                  '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n' \
                  '    usage: \n' \
                  '    python sqs.py -q <QueueName> -f <FileName>\n' \
                  '    python sqs.py -q <QueueName> -b <BucketName>'

    required_params = [['-q', '--queueName', 'Specify the name of the queue.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args = parsing(description, required_params, optional_params)

    # If the config file cannot be loaded, boto3 will use the credentials from ~/.aws/credentials
    config_parsing_was_successful, region_name_for_logs = load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    session = boto3.Session()
    s3_client = session.client('s3')

    return args, region_name_for_logs, s3_client


def scan_queue(queue_name):
    sqs = boto3.resource('sqs', region_name='local', aws_access_key_id='asd', aws_secret_access_key='asd',
                         endpoint_url='http://localhost:8001')
    #sqs = boto3.resource('sqs', region_name='eu-west-1')
    #queue_name = 'mrupdater-notifs'
    print('queuename: {}'.format(queue_name))

    queue = sqs.create_queue(QueueName=queue_name)

    # get messages
    msgs = []
    while True:
        messages = queue.receive_messages(VisibilityTimeout=120, WaitTimeSeconds=60)
        for message in messages:
            print(message.body)
            msgs.append(message.body)
        if not messages or len(msgs) > 100:
            break
    return msgs


def main():

    args, region_name_for_logs, s3_client = init()

    if args['queueName']:
        queue_name = str(args['queueName'])
    else:
        print ("Please specify a queue name.")
        sys.exit()

    data = scan_queue(queue_name)
    filenames = write_to_file('sqs', queue_name, data)

    bucket_upload(args['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
