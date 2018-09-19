import boto3
from botocore.exceptions import ClientError
import os
import argparse
from argparse import RawTextHelpFormatter
import json
import sys


def init():
    parser = argparse.ArgumentParser(
        description='[*] Scanner for DynamoDB tables.\n'
                    '[*] The results are saved to $currentpath/dynamodb_scan folder.\n'
                    '[*] If a bucket is provided, the results are uploaded to the bucket. \n\n'
                    'usage: \n    '
                    'python dynamo.py -t <TableName>\n    '
                    'python dynamo.py -t <TableName> -b <BucketName>',
        formatter_class=RawTextHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-t', '--tableName', help='Specify the name of the table.', required=True)
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-b', '--bucketName', help='Specify the name of the bucket.', required=False)

    args = vars(parser.parse_args())

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables
    # contain nonesens ("N/A")
    config_parsing_was_successful, region_name_for_logs = load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    session = boto3.Session()
    s3_client = session.client('s3')

    return args, region_name_for_logs, s3_client


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
        region_name_for_logs = config_json["region_name_for_logs"]
    except Exception as e:
        print("Error parsing 'region_name_for_logs' from the config file: {}".format(e))
        sys.exit()

    return True, region_name_for_logs


def scan_table(table, region_name_for_logs):

    dynamo = boto3.client('dynamodb', region_name=region_name_for_logs)

    try:
        response = dynamo.scan(TableName=table)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            print('Requested table not found.')
        sys.exit()

    print('Scanning the table...')
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = dynamo.scan(TableName=table, ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def write_to_file(table, data):

    print('Writing files to currentpath/scan_results folder...')
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'dynamodb_scan')
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    count = 1
    filenames = []

    while len(data) > 0:

        if len(data) <= 1000:
            file_name = final_directory + '/' + table + '-' + str(count) + '-' + str(count+999) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data:
                    f.write(json.dumps(line))
                del data[:]

        else:
            file_name = final_directory + '/' + table + str(count) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data[:1000]:
                    f.write(json.dumps(line))
                del data[:1000]
        count += 1000

    print('Files can be found in currentpath/dynamodb_scan folder.')

    return filenames


def upload_files(s3_client, filenames, bucket_name):

    print('Uploading files...')
    for f in filenames:
        try:
            key = f.split('/')[-2:]
            key = key[0] + '/' + key[1]
            tc = boto3.s3.transfer.TransferConfig()
            t = boto3.s3.transfer.S3Transfer(client=s3_client, config=tc)
            t.upload_file(f, bucket_name, key)
        except:
            print('File upload is not successful')


def main():

    args, region_name_for_logs, s3_client = init()

    if args['tableName']:
        table = str(args['tableName'])
    else:
        print ("Please specify a table name.")
        sys.exit()

    data = scan_table(table, region_name_for_logs)
    filenames = write_to_file(table, data)

    if args['bucketName']:
        bucket_name = args['bucketName']
        try:
            upload_files(s3_client, filenames, bucket_name)
            print ("Files are uploaded to the given bucket.")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
