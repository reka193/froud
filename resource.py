import skew
from skew.arn import ARN
from prettytable import PrettyTable
import requests
import sys
import json
import os
import argparse
from argparse import RawTextHelpFormatter

import logging
from logging.handlers import SysLogHandler
from logging import Formatter

# Syslog handler
syslog = SysLogHandler(address='/dev/log')
syslog.setLevel(logging.DEBUG)
syslog.setFormatter(Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S'))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(syslog)

parser = argparse.ArgumentParser(
    description='[*] List of available services.\n'
                '[*] The results can be filtered by the name of the service. Default value: [dynamodb, s3, sqs]'
                '\n\nusage: \n    python resource.py -s <ServiceName>',
    formatter_class=RawTextHelpFormatter)
parser.add_argument('-s', '--service', help='Filter the type of services by choosing from {dynamodb, s3, sqs}. At a time, only one service can be used for filtering.', required=False)

args = vars(parser.parse_args())


def init():
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


def enum_resources(arn, services):
    print('Enumerating all resources in the following services: ' + ', '.join(services) + '\n')

    values = []

    for service in services:
        arn.service.pattern = service
        try:
            instances = skew.scan('{}/*'.format(arn))
            if instances:
                for instance in instances:
                    region = str(instance).split(':')[3]
                    resource_name = str(instance).split('/')[1]
                    values.append([service, region, resource_name])

        except Exception as e:
            print(e)
    return values


def print_table(values, fieldnames):
    values.sort()
    x = PrettyTable()
    x.field_names = fieldnames

    for field in fieldnames:
        x.align[field] = "l"

    for value in values:
        x.add_row(value)

    print(x)


def main():
    init()
    arn = ARN()
    if not args['service']:
        services = ['s3', 'dynamodb', 'sqs']
    elif args['service'] in ['s3', 'dynamodb', 'sqs']:
        services = [args['service']]
    else:
        print('Invalid service.')
        sys.exit()

    services.sort()
    values = enum_resources(arn, services)

    print('\nAvailable resources: \n')
    print_table(values, ["Service", "Region", "Name"])


if __name__ == '__main__':
    main()
