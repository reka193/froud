import boto3
import sys
import json
import requests
import os
import argparse
from argparse import RawTextHelpFormatter
from boto3.exceptions import S3UploadFailedError
from prettytable import PrettyTable


def init(description, client_type, optional_params=None, required_params=None):
    if client_type in ["dynamodb", "sqs"]:
        optional_params = [['-b', '--bucketName', 'Specify the name of the bucket.']]
        if client_type == "dynamodb":
            required_params = [['-t', '--tableName', 'Specify the name of the table.']]
        else:
            required_params = [['-q', '--queueName', 'Specify the name of the queue.']]

    args = parsing(description, optional_params=optional_params, required_params=required_params)
    config_success, data = load_config_json("conf.json")
    client, s3_client = create_client(config_success, data, client_type)

    return args, client, s3_client


def parsing(description, required_params=None, optional_params=None):
    parser = argparse.ArgumentParser(description, formatter_class=RawTextHelpFormatter)
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    if required_params:
        add_params(required, required_params, True)
    if optional_params:
        add_params(optional, optional_params, False)

    args = vars(parser.parse_args())
    return args


def add_params(pars, params, req):
    for par in params:
        pars.add_argument(par[0], par[1], help=par[2], required=req)
    return pars


def init_keys():
    access_key_id = get_keys_and_token("AccessKeyId")
    secret_access_key = get_keys_and_token("SecretAccessKey")
    token = get_keys_and_token("Token")

    return access_key_id, secret_access_key, token


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


def load_config_json(config_json_filename, sqs=None):
    data = []
    try:
        with open(config_json_filename, 'r') as f:
            try:
                config_json = json.load(f)
            except Exception as e:
                print("Error parsing config file: {}".format(e))
                print("Using shared credentials and config file (~/.aws/..).")
                return False, data
    except IOError:
        print("Config file not found, using shared credentials and config file (~/.aws/..).")
        return False, data

    try:
        data.append(config_json["DEFAULT"]["aws_access_key_id"])
        data.append(config_json["DEFAULT"]["aws_secret_access_key"])
        data.append(config_json["DEFAULT"]["aws_session_token"])
        data.append(config_json["DEFAULT"]["region"])

        if sqs:
            data.append(config_json["SQS"]["fuzz_endpoint_url"])
            data.append(config_json["SQS"]["sqs_message"])

    except KeyError as key:
        print("Error parsing the config file: {}".format(key))
        sys.exit()

    return True, data


def create_client(config_success, data, client_type):
    if not config_success:
        session = boto3.Session()
        client = session.client(client_type)
        s3_client = session.client('s3')
    else:
        aws_access_key_id, aws_secret_access_key, aws_session_token, region_name = data
        session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key,
                                aws_session_token=aws_session_token)

        try:
            client = session.client(client_type, region_name)
            s3_client = session.client('s3')
        except ValueError as error:
            print('Error: {}'.format(error))
            sys.exit()
    return client, s3_client


def write_to_file_1000(service, resource_name, data):

    print('Writing files...')
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


def bucket_upload(bucket, s3_client, filenames):
    if bucket:
        bucket_name = bucket
        try:
            upload_files(s3_client, filenames, bucket_name)
        except Exception as e:
            print(e)


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


def exception(error, fail):
    print(fail)
    resp = error.response['Error']['Code']
    if resp == 'AccessDenied':
        print('Required AWS permission is missing: {}\n'.format(resp))
    else:
        print('{}'.format(resp))
    sys.exit()
