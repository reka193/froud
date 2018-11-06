import skew
from skew.arn import ARN
import boto3
from prettytable import PrettyTable
import json
import os
import sys
import requests
from argparse import RawTextHelpFormatter
import argparse
import logging
from logging.handlers import SysLogHandler
from logging import Formatter
from common import init_keys

# Syslog handler
syslog = SysLogHandler(address='/dev/log')
syslog.setLevel(logging.DEBUG)
syslog.setFormatter(Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S'))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(syslog)


def init():
    init_keys()
    parser = argparse.ArgumentParser(
            description='[*] S3 policy enumerator.\n'
                        '[*] Returned policy attributes:\n'
                        '   [+] Name: The name of the policy.\n'
                        '   [+] Sid: The Sid (statement ID) is an optional identifier for the policy statement.\n'
                        '   [+] Action: Describes the specific action(s) that will be allowed or denied.\n'
                        '   [+] Principal: Specifies the entity that is allowed or denied access to a resource.\n'
                        '   [+] Resource: Specifies the object or objects that the statement covers.\n'
                        '   [+] Effect: Specifies whether the statement results in an allow or an explicit deny',
            formatter_class=RawTextHelpFormatter)

    args = parser.parse_args()
    return args


def enum_resources(arn, services):
    print('Enumerating s3 policies...' + '\n')

    values_pol = []
    for service in services:
        arn.service.pattern = service
        try:
            instances = skew.scan('{}/*'.format(arn))
            if instances:
                for instance in instances:
                    region = str(instance).split(':')[3]
                    resource_name = str(instance).split('/')[1]

                    s3 = boto3.resource('s3')
                    bucket = s3.Bucket(resource_name)
                    try:
                        pol = json.loads(s3.BucketPolicy(bucket.name).policy)
                        values_pol.append(json.dumps(pol['Statement'][0], indent=4, sort_keys=True))
                    except:
                        pass
        except Exception as e:
            print(e)
    return values_pol


def print_table(values, fieldnames):

    nums = range(len(values))

    values.sort()
    for num in nums:
        values[num].insert(0, num+1)

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
    services = ['s3']
    services.sort()
    values_pol = enum_resources(arn, services)

    print('\nAttached S3 policies: \n')

    # for sublst in values_pol:
    #     print(" | ".join(str(bit) for bit in sublst))

    for item in values_pol:
        print(item)
    #print_table(values_pol, ["No.", "Name", "Sid", "Action", "Principal", "Resource", "Effect"])
    #print_table(values_pol2, ["No.", "Name", "Resource", "Effect"])


if __name__ == '__main__':
    main()
