from botocore.exceptions import ClientError
import common
import sys


def init():

    description = '\n[*] SQS message scanner.\n' \
                  '[*] Specify the name of the queue to save the messages from.\n' \
                  '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n'

    required_params = [['-q', '--queueName', 'Specify the name of the queue.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args = common.parsing(description, required_params, optional_params)

    config_success, data = common.load_config_json("conf.json")

    # If the config file can not be found, shared credentials are used from ~/.aws/credentials and /config
    sqs_client, s3_client = common.create_client(config_success, data, 'sqs')

    return args, sqs_client, s3_client


def scan_queue(queue_name, sqs):
    try:
        queue = sqs.create_queue(QueueName=queue_name)
    except ClientError as err:
        print(err)
        sys.exit()

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

    args, sqs, s3_client = init()

    queue_name = str(args['queueName'])

    data = scan_queue(queue_name, sqs)
    filenames = common.write_to_file_1000('sqs', queue_name, data)

    if args['bucketName']:
        common.bucket_upload(args['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
