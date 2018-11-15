import boto3
from botocore.exceptions import ClientError
import sys
import common


def init():
    description = "\n[*] Scanner for DynamoDB tables.\n" \
                  "[*] The results will be saved to $currentpath/dynamodb_scan folder.\n" \
                  "[*] If a bucket is provided, the results are uploaded to the bucket. \n\n"
    required_params = [['-t', '--tableName', 'Specify the name of the table.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args = common.parsing(description, required_params, optional_params)

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables
    # contain nonsense ("N/A")
    config_parsing_was_successful, region_name_for_logs = common.load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    session = boto3.Session()
    s3_client = session.client('s3')

    common.init_keys()

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

    table = str(args['tableName'])

    data = scan_table(table, region_name_for_logs)
    filenames = common.write_to_file('dynamodb', table, data)

    common.bucket_upload(args['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
