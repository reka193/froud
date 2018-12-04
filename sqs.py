from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
import common
import sys


def scan_queue(queue_name, sqs):
    try:
        queue = sqs.create_queue(QueueName=queue_name)
    except EndpointConnectionError as error:
        print('The requested queue could not be reached. \n{}'.format(error))
        sys.exit()
    except ClientError as error:
        common.exception(error, 'Queue could not be reached. \n{}'.format(error))
    # get messages
    msgs = []
    while True:
        messages = queue.receive_messages(VisibilityTimeout=120, WaitTimeSeconds=60)
        for message in messages:
            msgs.append(message.body)
        if not messages or len(msgs) > 100:
            break
    return msgs


def main():

    description = '\n[*] SQS message scanner.\n' \
                  '[*] Specify the name of the queue to save the messages from.\n' \
                  '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n'

    args, sqs, s3_client = common.init(description, 'sqs')

    data = scan_queue(str(args['queueName']), sqs)

    filenames = common.write_to_file_1000('sqs', str(args['queueName']), data)

    if args['bucketName']:
        common.bucket_upload(args['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
