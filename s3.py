import boto3
from botocore.exceptions import ClientError
from prettytable import PrettyTable
import argparse
from argparse import RawTextHelpFormatter
import sys

parser = argparse.ArgumentParser(description=' !!! DESCRIPTION GOES HERE !!! \n\nExample: \n    python s3.py -b theNameOfTheBucket', formatter_class=RawTextHelpFormatter)
parser.add_argument('-b', '--bucketName', help='The name of the bucket.', required=True)
args = vars(parser.parse_args())


def list_grants(s3, bucket_name):

    try:
        objects = s3.list_objects_v2(Bucket=bucket_name)
        print('Collecting objects and the ACL...\n')
        print('The number of objects in the bucket: {}\n'.format(len(objects)))
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'InvalidBucketName':
            print('The specified bucket is not valid.')
        if ce.response['Error']['Code'] == 'AccessDenied':
            print('\nNo permission to get list objects.')
        sys.exit()
    try:
        bucket_acl = s3.get_bucket_acl(Bucket=bucket_name)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'InvalidBucketName':
            print('The specified bucket is not valid.')
        if ce.response['Error']['Code'] == 'AccessDenied':
            print('\nNo permission to get bucket acl.')
        sys.exit()

    grants = bucket_acl['Grants']

    values = []

    for grant in grants:
        grant_type = grant['Grantee']['Type']
        grant_permission = grant['Permission']
        values.append([grant_type, grant_permission])

    print_table(values, ['Type', 'Permission'])

    try:
        for obj in objects['Contents']:
            object_acl = s3.get_object_acl(Bucket=bucket_name, Key=obj['Key'])
            print(object_acl)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'AccessDenied':
            print('\nNo permission to get object acl.')


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


def make_bucket_public(s3, bucket_name):
    try:
        s3.put_bucket_acl(
            ACL='public-read',
            Bucket=bucket_name,
        )
        print('The bucket has been made public.')
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'AccessDenied':
            print('\nNo permission to make the bucket public.')


if __name__ == '__main__':
    bucket_name = args['bucketName']
    s3 = boto3.client('s3')
    list_grants(s3, bucket_name)
    make_bucket_public(s3, bucket_name)
