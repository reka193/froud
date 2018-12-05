from botocore.exceptions import ClientError
import common
import sys
from botocore.exceptions import EndpointConnectionError


def scan_table(table, dynamo):

    try:
        response = dynamo.scan(TableName=table)
    except EndpointConnectionError as error:
        print('The requested queue could not be reached. \n{}'.format(error))
        sys.exit()
    except ClientError as error:
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            print('Requested table not found.')
        else:
            common.exception(error, 'Scan dynamodb table failed.')

    print('Scanning the table...')
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = dynamo.scan(TableName=table, ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def main():
    description = "\n[*] Scanner for DynamoDB tables.\n" \
                      "[*] The results will be saved to $currentpath/dynamodb_scan folder.\n" \
                      "[*] If a bucket is provided, the results are uploaded to the bucket. \n\n"

    arguments, dynamo_client, s3_client = common.init(description, 'dynamodb')

    table = str(arguments['tableName'])

    data = scan_table(table, dynamo_client)
    filenames = common.write_to_file_1000('dynamodb', table, data)

    if arguments['bucketName']:
        common.bucket_upload(arguments['bucket'], s3_client, filenames)


if __name__ == '__main__':
    main()
