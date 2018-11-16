from botocore.exceptions import ClientError
import sys
import common


def scan_table(table, dynamo):

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


def init():
    description = "\n[*] Scanner for DynamoDB tables.\n" \
                  "[*] The results will be saved to $currentpath/dynamodb_scan folder.\n" \
                  "[*] If a bucket is provided, the results are uploaded to the bucket. \n\n"

    required_params = [['-t', '--tableName', 'Specify the name of the table.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args = common.parsing(description, required_params, optional_params)

    config_success, data = common.load_config_json("conf.json")

    # If the config file can not be found, shared credentials are used from ~/.aws/credentials and /config
    dynamo_client, s3_client = common.create_client(config_success, data, 'dynamodb')

    return args, dynamo_client, s3_client


def main():
    description = "\n[*] Scanner for DynamoDB tables.\n" \
                      "[*] The results will be saved to $currentpath/dynamodb_scan folder.\n" \
                      "[*] If a bucket is provided, the results are uploaded to the bucket. \n\n"

    required_params = [['-t', '--tableName', 'Specify the name of the table.']]
    optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]

    args, dynamo_client, s3_client = common.init(description, 'sqs', optional_params=optional_params,
                                                 required_params=required_params)

    data = scan_table(str(args['tableName']), dynamo_client)
    filenames = common.write_to_file_1000('dynamodb', str(args['tableName']), data)

    if args['bucketName']:
        common.bucket_upload(args['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
