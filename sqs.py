import boto3
import sys
import argparse
from argparse import RawTextHelpFormatter
from common import upload_files
from common import load_config_json
from common import write_to_file
from common import init_keys


def init():
    #init_keys()
    parser = argparse.ArgumentParser(description='[*] SQS message scanner.\n'
                                                 '[*] Specify the name of the queue to save the messages from.\n'
                                                 '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n'
                                                 '\n\nusage: \n    python sqs.py -q <QueueName> -f <FileName>\n'
                                                 'python sqs.py -q <QueueName> -b <BucketName>',
                                     formatter_class=RawTextHelpFormatter)

    required = parser.add_argument_group('required arguments')
    required.add_argument('-q', '--queueName', help='Specify the name of the queue.', required=True)
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-b', '--bucketName', help='Specify the name of the bucket.', required=False)

    args = vars(parser.parse_args())

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables
    # contain nonsense ("N/A")
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

    if args['bucketName']:
        bucket_name = args['bucketName']
        try:
            upload_files(s3_client, filenames, bucket_name)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
