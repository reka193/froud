import boto3
import datetime
import re
import os
import sys
from prettytable import PrettyTable
from common import upload_files
from common import load_config_json
from common import init_keys
from common import parsing


def init():
    description = '[*] Cloudwatch log scanner.\n'
    '[*] The results are saved to $currentpath/cw_logs folder.\n'
    '[*] The logs are read for a specified number of hours until the current time. Default value: 24 hours.\n'
    '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n'
    '   usage: \n    '
    '   python cloudwatch.py -t <TimeInHours>\n'
    '   python cloudwatch.py -b <BucketName>'
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.'],
                       ['-t', '--time', 'Specify the number of hours to read the logs '
                                        'until the current time. Default value: 24 hours.']]

    args = parsing(description, optional_params=optional_params)

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables contain nonesens ("N/A")
    config_parsing_was_successful, region_name_for_logs = load_config_json(
        "conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    init_keys()

    logs_client = boto3.client('logs', region_name=region_name_for_logs)

    return args, region_name_for_logs, logs_client


def list_and_save(logs_client, args):
    groups = logs_client.describe_log_groups()['logGroups']
    values = []
    filenames = []

    if args['time']:
        hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=int(args['time']))
    else:
        hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    start_time = int(hours_ago.strftime("%s")) * 1000
    stop_time = int(datetime.datetime.utcnow().strftime("%s")) * 1000

    for group in groups:
        group_name = group['logGroupName']
        streams = logs_client.describe_log_streams(logGroupName=group_name)['logStreams']
        for stream in streams:
            stream_name = stream['logStreamName']
            values.append(str(group_name))

            log_events = logs_client.get_log_events(logGroupName=group_name, logStreamName=stream_name,
                                                    startTime=start_time, endTime=stop_time)
            events = log_events['events']

            groupname = re.sub('[^\w\s-]', '', group_name)
            streamname = re.sub('[^\w\s-]', '', stream_name)
            gr_st = groupname + '--' + streamname

            current_directory = os.getcwd()
            final_directory = os.path.join(current_directory, r'cw_logs')
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)

            try:
                message = ''
                for event in events:
                    if event['message']:
                        message = message + event['message'] + '\n'
                if message:
                    file_name = final_directory + '/' + gr_st + '.txt'
                    filenames.append(file_name)
                    with open(file_name, 'w+') as f:
                        f.write(message)

            except Exception as e:
                print('File is skipped: {}, due to: {}'.format(file_name, e))
    print('Files downloaded to $currentpath/cw_logs folder.')
    values = set(values)

    return filenames, values


def print_table(values):
    nums = range(len(values))
    nums = [x + 1 for x in nums]
    values_to_print = [list(a) for a in zip(nums, values)]

    values_to_print.sort()
    x = PrettyTable()
    x.field_names = ["No.", "Groups"]
    x.align["Groups"] = "l"

    for value in values_to_print:
        x.add_row(value)

    print('\nAvailable Cloudwatch logs: \n')
    print(x)


def main():
    args, region_name_for_logs, logs_client = init()

    try:
        print('Collecting CloudWatch logs...')
        filenames, values = list_and_save(logs_client, args)

    except:
        print('Error collecting logs.')
        sys.exit()

    print_table(values)

    try:
        session = boto3.Session()
        s3_client = session.client('s3')

        if args['bucketName']:
            bucket_name = args['bucketName']
            if filenames:
                upload_files(s3_client, filenames, bucket_name)
            else:
                print('There are no files to upload.')
    except:
        print('Error while creating the S3 client.')


if __name__ == '__main__':
    main()
