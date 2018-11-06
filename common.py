import boto3
from boto3.exceptions import S3UploadFailedError


def upload_files(s3_client, filenames, bucket_name):

    print('Uploading files to the bucket {}...'.format(bucket_name))
    for f in filenames:
        try:
            key = f.split('/')[-2:]
            key = key[0] + '/' + key[1]
            tc = boto3.s3.transfer.TransferConfig()
            t = boto3.s3.transfer.S3Transfer(client=s3_client, config=tc)
            t.upload_file(f, bucket_name, key, extra_args={'ACL': 'public-read'})

            file_url = 'https://{}.s3.amazonaws.com/{}'.format(bucket_name, key)
            print('The uploaded file is public and accessible with the following url: \n    {}'.format(file_url))
        except S3UploadFailedError:
            print('File upload is not successful: PutObject permission missing.')
