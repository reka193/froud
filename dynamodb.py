import boto3
from botocore.exceptions import ClientError
import argparse
from argparse import RawTextHelpFormatter
import sys
from common import upload_files
from common import load_config_json
from common import init_keys
from common import write_to_file
from common import parsing


def init():
    description = "[*] Scanner for DynamoDB tables.\n " \
                "[*] The results are saved to $currentpath/dynamodb_scan folder.\n" \
                "[*] If a bucket is provided, the results are uploaded to the bucket. \n\n" \
                "   usage: \n" \
                "   python dynamodb.py -t <TableName>\n" \
                "   python dynamodb.py -t <TableName> -b <BucketName>"
    required_params = [['-t', '--tableName', 'Specify the name of the table.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args = parsing(description, required_params, optional_params)

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables
    # contain nonesens ("N/A")
    config_parsing_was_successful, region_name_for_logs = load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    session = boto3.Session()
    s3_client = session.client('s3')

    init_keys()

    return args, region_name_for_logs, s3_client


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


def main():

    args, region_name_for_logs, s3_client = init()

    if args['tableName']:
        table = str(args['tableName'])
    else:
        print ("Please specify a table name.")
        sys.exit()

    data = scan_table(table, region_name_for_logs)
    filenames = write_to_file('dynamodb', table, data)

    if args['bucketName']:
        bucket_name = args['bucketName']
        try:
            upload_files(s3_client, filenames, bucket_name)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
