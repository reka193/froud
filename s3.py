import boto3
from prettytable import PrettyTable
import argparse
from argparse import RawTextHelpFormatter
from boto3.exceptions import S3UploadFailedError

parser = argparse.ArgumentParser(description='[*] File upload to S3.\n'
                                             '[*] Specify the name of the file you are uploading and the destination bucket.\n'
                                             '[*] The key of the object can be set, but not required. Default value: the name of the file.'
                                             '\n\nusage: \n    python s3.py -b <BucketName> -f <FileName>\n'
                                             '    python s3.py -b <BucketName> -f <FileName> -k <Key>', formatter_class=RawTextHelpFormatter)


def init():
    required = parser.add_argument_group('required arguments')
    required.add_argument('-b', '--bucketName', help='The name of the bucket.', required=True)
    required.add_argument('-f', '--fileName', help='The name of the file to upload.', required=True)
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-k', '--key', help='The key of the object in the bucket. Default value: fileName',
                          required=False)

    args = vars(parser.parse_args())
    return args


def print_table(values, fieldnames):
    values.sort()
    x = PrettyTable()
    x.field_names = fieldnames
    for field in fieldnames:
        x.align[field] = "l"

    for value in values:
        x.add_row(value)
    print('The following ACL belongs to the bucket:')
    print(x)


def upload_file(s3_client, file_name, bucket_name, args):

    if args['key']:
        key = args['key']
    else:
        key = file_name

    print('Uploading files...')

    try:
        tc = boto3.s3.transfer.TransferConfig()
        t = boto3.s3.transfer.S3Transfer(client=s3_client, config=tc)
        t.upload_file(file_name, bucket_name, key, extra_args={'ACL': 'public-read'})

        file_url = 'https://{}.s3.amazonaws.com/{}'.format(bucket_name, key)
        print('The uploaded file is public and accessible with the following url: {}'.format(file_url))
    except S3UploadFailedError as ex:
        if ex.response['Error']['Code'] == 'AccessDenied':
            print('File upload is not successful: PutObject permission missing.')


def main():
    args = init()
    bucket_name = args['bucketName']
    s3 = boto3.client('s3')

    if args['fileName']:
        file_name = args['fileName']
    else:
        print('Filename not specified or invalid filename.')

    upload_file(s3, file_name, bucket_name, args)


if __name__ == '__main__':
    main()
