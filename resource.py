import skew
from skew.arn import ARN
import boto3
from prettytable import PrettyTable

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

arn = ARN()
services = ['s3', 'dynamodb', 'sqs']
services.sort()

print('Enumerating all resources in the following services: ' + ', '.join(services) + '\n')

values = []
for service in services:
    arn.service.pattern = service
    try:
        instances = skew.scan('{}/*'.format(arn))
        print('arn: {}'.format(arn))
        if instances:
            for instance in instances:
                print(instance)
                region = str(instance).split(':')[3]
                queue_name = str(instance).split('/')[1]
                values.append([service, region, queue_name])

    except Exception as e:
        print(e)

values.sort()
x = PrettyTable()
x.field_names = ["Service", "Region", "Name"]
x.align["Service"] = "l"
x.align["Region"] = "l"
x.align["Name"] = "l"

for value in values:
    x.add_row(value)

print('\nAvailable resources: \n')
print(x)
