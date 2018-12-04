import skew
from skew.arn import ARN
import sys
import argparse
from argparse import RawTextHelpFormatter
import common
from botocore.exceptions import ClientError


def init():
    common.init_keys()

    parser = argparse.ArgumentParser(
        description='\n[*] List of available resources.\n'
                    '[*] The results can be filtered by the name of the service. Default value: [dynamodb, s3, sqs]',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-s', '--service', help='Filter the type of services by choosing from {dynamodb, s3, sqs}. At '
                                                'a time, only one service can be used for filtering.', required=False)

    args = vars(parser.parse_args())

    return args


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
        except ClientError as error:
            resp = error.response['Error']['Code']
            if resp == 'ExpiredTokenException':
                print('AWS token has expired: \n{}'.format(error))
            else:
                print('{}'.format(resp))
            sys.exit()

    return values


def main():
    args = init()
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
    common.print_table(values, ["Service", "Region", "Name"])


if __name__ == '__main__':
    main()
