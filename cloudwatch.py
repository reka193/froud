import boto3
import datetime
import re
import os
import sys
import json
import argparse
from argparse import RawTextHelpFormatter

from prettytable import PrettyTable

import logging
from logging.handlers import SysLogHandler
from logging import Formatter


parser = argparse.ArgumentParser(description=' !!! DESCRIPTION GOES HERE !!! \n\nExample: \n    python cloudw.py -b nameOfMyBucket', formatter_class=RawTextHelpFormatter)
parser.add_argument('-b', '--bucketName', help='Specify the name of the bucket.', required=False)
args = vars(parser.parse_args())

syslog = SysLogHandler(address='/dev/log')
syslog.setLevel(logging.DEBUG)
syslog.setFormatter(Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S'))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(syslog)


def load_config_json(config_json_filename):
    try:
        with open(config_json_filename) as config_file_handler:
            try:
                config_json = json.load(config_file_handler)
            except Exception as e:
                print("Error parsing config file: {}".format(e))
                sys.exit()
    except Exception as e:
        print("Error opening file: {}".format(e))
        return False

    try:
        region_name = config_json["region_name"]
    except Exception as e:
        print("Error parsing 'region_name' from the config file: {}".format(e))
        sys.exit()

    try:
        aws_access_key_id = config_json["aws_access_key_id"]
    except Exception as e:
        print("Error parsing 'aws_access_key_id' from the config file: {}".format(e))
        sys.exit()

    try:
        aws_secret_access_key = config_json["aws_secret_access_key"]
    except Exception as e:
        print("Error parsing 'aws_secret_access_key' from the config file: {}".format(e))
        sys.exit()

    try:
        upload_endpoint_url = config_json["upload_endpoint_url"]
    except Exception as e:
        print("Error parsing 'upload_endpoint_url' from the config file: {}".format(e))
        sys.exit()

    try:
        region_name_for_logs = config_json["region_name_for_logs"]
    except Exception as e:
        print("Error parsing 'region_name_for_logs' from the config file: {}".format(e))
        sys.exit()

    return True, region_name, aws_access_key_id, aws_secret_access_key, upload_endpoint_url, region_name_for_logs


def list_and_save(logs):
    try:

        groups = logs.describe_log_groups()['logGroups']
        values = []
        filenames = []

        hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        start_time = int(hours_ago.strftime("%s")) * 1000
        stop_time = int(datetime.datetime.utcnow().strftime("%s")) * 1000

        for group in groups:
            group_name = group['logGroupName']
            streams = logs.describe_log_streams(logGroupName=group_name)['logStreams']
            for stream in streams:
                stream_name = stream['logStreamName']
                values.append(str(group_name))

                log_events = logs.get_log_events(logGroupName=group_name, logStreamName=stream_name, startTime = start_time, endTime = stop_time)
                events = log_events['events']

                gr_st = group_name + '/' + stream_name
                gr_st = re.sub('[^\w\s-]', '', gr_st)

                current_directory = os.getcwd()
                final_directory = os.path.join(current_directory, r'logs')
                if not os.path.exists(final_directory):
                    os.makedirs(final_directory)

                file_name = final_directory + '/' + gr_st + '.txt'
                filenames.append(file_name)

                try:
                    message = ''
                    for event in events:
                        if event['message']:
                            message = message + event['message'] + '\n'
                    if message:
                        with open(file_name, 'w+') as f:
                            f.write(message)

                except Exception as e:
                    print('File is skipped: {}, due to: {}'.format(file_name, e))
        print('Files downloaded to currentpath/logs folder.')
        values = set(values)
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
    nums = range(len(values))
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
    # If the config file cannot be loaded then boto3 will use its cached data because the global variables contain nonesens ("N/A")
    config_parsing_was_successfull, region_name, aws_access_key_id, aws_secret_access_key, upload_endpoint_url, region_name_for_logs = load_config_json(
        "conf.json")

    if not config_parsing_was_successfull:
        region_name = "N/A"
        aws_access_key_id = "N/A"
        aws_secret_access_key = "N/A"
        upload_endpoint_url = "N/A"
        region_name_for_logs = "N/A"

    try:
        logs = boto3.client('logs', region_name=region_name_for_logs)

    except:
        print('Error while creating the Cloudwatch client.')

    try:
        print('Collecting CloudWatch logs...')
        filenames, values = list_and_save(logs)

    except:
        print('Error collecting logs.')

    try:
        print_table(values)
    except Exception as e:
        print("Error creating table: {}".format(e))

    try:
        session = boto3.Session()
        s3_client = session.client('s3', region_name=region_name, aws_access_key_id=aws_access_key_id or None,
                                   aws_secret_access_key=aws_secret_access_key or None,
                                   endpoint_url=upload_endpoint_url)

        if args['bucketName']:
            bucket_name = args['bucketName']
            print ("Bucketname provided. Files will be uploaded.")
            upload_files(s3_client, filenames, bucket_name)
        else:
            print("Bucketname has not been provided. Files will not be uploaded.")

    except:
        print('Error while creating the S3 client.')


if __name__ == '__main__':
    main()
