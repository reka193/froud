import boto3
import datetime
import re
import os

from prettytable import PrettyTable

import logging
from logging.handlers import SysLogHandler
from logging import Formatter

# Syslog handler
# syslog = SysLogHandler(address='/dev/log')
# syslog.setLevel(logging.DEBUG)
# syslog.setFormatter(Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
#                               '%m-%d %H:%M:%S'))
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(syslog)


hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
start_time = int(hours_ago.strftime("%s"))
stop_time = int(datetime.datetime.utcnow().strftime("%s"))


# start_time = int(hours_ago.replace(minute=0, second=0, microsecond=0).strftime("%s")) * 1000
# stop_time = int(hours_ago.replace(minute=59, second=59).strftime("%s")) * 1000 + 999


def list_and_save(logs):
    try:

        groups = logs.describe_log_groups()['logGroups']
        values = []
        filenames = []

        for group in groups:
            group_name = group['logGroupName']
            streams = logs.describe_log_streams(logGroupName=group_name)['logStreams']
            for stream in streams:
                stream_name = stream['logStreamName']
                values.append(str(group_name))

                log_events = logs.get_log_events(logGroupName=group_name, logStreamName=stream_name)
                events = log_events['events']

                gr_st = group_name + '/' + stream_name
                gr_st = re.sub('[^\w\s-]', '', gr_st)

                current_directory = os.getcwd()
                final_directory = os.path.join(current_directory, r'logs')
                if not os.path.exists(final_directory):
                    os.makedirs(final_directory)

                file_name = final_directory + '/' + gr_st + '.txt'
                filenames.append(file_name)

                # print('Writing to file: {}'.format(file_name))
                try:
                    with open(file_name, 'w+') as f:
                        for event in events:
                            message = event['message']
                            f.write(message + '\n')
                except Exception as e:
                    print('File is skipped: {}, due to: '.format(file_name, e))
        print('Files downloaded to currentpath/logs folder.')
        return filenames, values

    except Exception as e:
            print(e)


def upload_files(s3_client, filenames, bucket_name):

        print('Uploading files...')
        for file in filenames:
            try:
                key = file.split('/')[-2:]
                key = key[0] + '/' + key[1]

                tc = boto3.s3.transfer.TransferConfig()
                t = boto3.s3.transfer.S3Transfer(client=s3_client, config=tc)

                t.upload_file(file, bucket_name, key)

            except:
                print('File upload is not successful')


def print_table(values):
    nums = []
    for num in range(len(values)):
        nums.append(num)

    values.sort()
    x = PrettyTable()
    x.field_names = ["No.", "Groups"]
    x.align["Groups"] = "l"

    for value in values:
        x.add_row(nums, value)

    print('\nAvailable Cloudwatch logs: \n')
    print(x)


if __name__ == '__main__':
    try:
        logs = boto3.client('logs', region_name='us-west-2')

    except:
        print('Error while creating the Cloudwatch client.')

    try:
        print('Collecting CloudWatch logs...')
        filenames, values = list_and_save(logs)

    except:
        print('Error collecting logs.')

    try:
        print_table(values)
        #print(values)
    except Exception as e:
        print("Error creating table: {}".format(e))

    try:
        session = boto3.Session()
        s3_client = session.client('s3', region_name='local', aws_access_key_id='asd' or None,
                                   aws_secret_access_key='asd' or None, endpoint_url='http://localhost:8000')
        #bucket_name =
        #upload_files(s3_client, filenames, bucket_name)

    except:
        print('Error while creating the S3 client.')
