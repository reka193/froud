import boto3
import sys
import json
import requests
import os
import argparse
from argparse import RawTextHelpFormatter
from boto3.exceptions import S3UploadFailedError
from prettytable import PrettyTable


def parsing(description, required_params=None, optional_params=None):
    parser = argparse.ArgumentParser(description, formatter_class=RawTextHelpFormatter)
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    if required_params:
        for req in required_params:
                required.add_argument(req[0], req[1], help=req[2], required=True)

    if optional_params:
        for opt in optional_params:
            optional.add_argument(opt[0], opt[1], help=opt[2], required=False)

    args = vars(parser.parse_args())
    return args


def init_keys():
    access_key_id = get_keys_and_token("AccessKeyId")
    secret_access_key = get_keys_and_token("SecretAccessKey")
    token = get_keys_and_token("Token")

    save_credentials(access_key_id, secret_access_key, token)


def get_keys_and_token(key):
    try:
        url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
        role = requests.get(url).text
        response = requests.get(url + str(role)).text
    except requests.exceptions.RequestException as e:
        print("Request error: {}".format(e))
        sys.exit()
    try:
        text = json.loads(response)
        final_request_value = text[key]
    except Exception as e:
        print("Error parsing " + str(key) + ": {}".format(e))
        sys.exit()
    return final_request_value


def save_credentials(access_key_id, secret_access_key, token):
    final_directory = '/home/ec2-user/.aws'

    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    file_name = final_directory + '/credentials'

    with open(file_name, 'w+') as f:
        f.write("[default]\naws_access_key_id = {}\naws_secret_access_key = {}\naws_session_token = {}\n".format(access_key_id, secret_access_key, token))


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


def print_table(values, fieldnames):
    values.sort()
    x = PrettyTable()
    x.field_names = fieldnames
    for field in fieldnames:
        x.align[field] = "l"

    for value in values:
        x.add_row(value)

    print(x)


def write_to_file(service, resource_name, data):

    print('Writing files...'.format(service))
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'{}_scan'.format(service))
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    count = 1
    filenames = []

    while len(data) > 0:

        if len(data) <= 1000:
            file_name = final_directory + '/' + resource_name + '-' + str(count) + '-' + str(count+999) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data:
                    f.write(json.dumps(line))
                del data[:]

        else:
            file_name = final_directory + '/' + resource_name + str(count) + '.txt'
            filenames.append(file_name)
            with open(file_name, 'w+') as f:
                for line in data[:1000]:
                    f.write(json.dumps(line))
                del data[:1000]
        count += 1000

    print('Files can be found in $currentpath/{}_scan folder.'.format(service))

    return filenames
