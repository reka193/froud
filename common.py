import boto3
import sys
import json
from boto3.exceptions import S3UploadFailedError


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
