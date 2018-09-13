import boto3
import os


def scan_table(table):
    dynamo = boto3.client('dynamodb', region_name='us-west-2')

    response = dynamo.scan(TableName=table)
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = dynamo.scan(TableName=table, ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def write_to_file(table, data):
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'scan_results')
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    count = 1
    filenames = []

    while len(data) > 0:

        if len(data) <= 1000:
            file_name = final_directory + '/' + table + str(count) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data:
                    f.write(str(line))
                del data[:]

        else:
            file_name = final_directory + '/' + table + str(count) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data[:1000]:
                    f.write(str(line))
                del data[:1000]
        count += 1

    return filenames


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


if __name__ == '__main__':
    table = 'lh-handsoff-hudevsxl-Url'
    data = scan_table(table)
    filenames = write_to_file(table, data)
    # upload_files(s3, filenames, bucket_name)
