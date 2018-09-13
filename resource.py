import skew
from skew.arn import ARN
import boto3
from prettytable import PrettyTable
import json

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


def enum_resources(services):
    print('Enumerating all resources in the following services: ' + ', '.join(services) + '\n')

    values = []
    values_pol = []
    for service in services:
        arn.service.pattern = service
        try:
            instances = skew.scan('{}/*'.format(arn))
            if instances:
                for instance in instances:
                    region = str(instance).split(':')[3]
                    resource_name = str(instance).split('/')[1]
                    values.append([service, region, resource_name])

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

                            values_pol.append([resource_name, sid, action, principal, resource, effect])
                        except:
                            pass
        except Exception as e:
            print(e)
    return values, values_pol


def print_table(values, fieldnames):
    values.sort()
    x = PrettyTable()
    x.field_names = fieldnames
    for field in fieldnames:
        x.align[field] = "l"

    for value in values:
        x.add_row(value)

    print(x)


if __name__ == '__main__':
    arn = ARN()
    # services = ['s3', 'dynamodb', 'sqs']
    services = ['sqs']
    services.sort()
    values, values_pol = enum_resources(services)

    print('\nAvailable resources: \n')
    print_table(values, ["Service", "Region", "Name"])
    if 's3' in services:
        print('\nAttached S3 policies: \n')
        print_table(values_pol, ["Name", "Sid", "Action", "Principal", "Resource", "Effect"])
