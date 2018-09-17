import skew
from skew.arn import ARN
import boto3
from prettytable import PrettyTable
import json
import os
import sys
import requests

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
    final_request_value = ""
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
    print('Enumerating all policies belonging to resources in the following services: ' + ', '.join(services) + '\n')

    values_pol = []
    values_pol2 = []
    for service in services:
        arn.service.pattern = service
        try:
            instances = skew.scan('{}/*'.format(arn))
            if instances:
                for instance in instances:
                    region = str(instance).split(':')[3]
                    resource_name = str(instance).split('/')[1]

                    if service == 's3':
                        s3 = boto3.resource('s3')
                        bucket = s3.Bucket(resource_name)
                        try:
                            pol = json.loads(s3.BucketPolicy(bucket.name).policy)
                            try:
                                sid = pol['Statement'][0]['Sid']
                            except:
                                sid = ''
                            action = pol['Statement'][0]['Action']
                            principal = pol['Statement'][0]['Principal']['AWS']
                            resource = pol['Statement'][0]['Resource']
                            effect = pol['Statement'][0]['Effect']

                            values_pol.append([resource_name, sid, action, principal])
                            values_pol2.append([resource_name, resource, effect])
                        except:
                            pass
        except Exception as e:
            print(e)
    return values_pol, values_pol2


def print_table(values, fieldnames):

    values.sort()
    for num in range(len(values)):
        values[num].insert(0, num)

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
    # services = ['s3', 'dynamodb', 'sqs']
    services = ['s3']
    services.sort()
    values_pol, values_pol2 = enum_resources(arn, services)

    if 's3' in services:
        print('\nAttached S3 policies: \n')
        print_table(values_pol, ["No.", "Name", "Sid", "Action", "Principal"])
        print_table(values_pol2, ["No.", "Name", "Resource", "Effect"])


if __name__ == '__main__':
    main()
