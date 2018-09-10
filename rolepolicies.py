from skew.arn import ARN
import boto3
import requests
import json
from prettytable import PrettyTable
import argparse

import logging
from logging.handlers import SysLogHandler
from logging import Formatter
import re



parser = argparse.ArgumentParser(description=' !!! DESCRIPTION GOES HERE !!! ')
parser.add_argument('-rft','--regex-filter-type', help='Select the column you wish to filter. E.g. "Service", "Action", "Resource", "Effect" or "Policy name".', required=True)
parser.add_argument('-rf','--regex-filter', help='Display only those entities that match the entered regular expression.', required=True)
args = vars(parser.parse_args())

# Syslog handler
syslog = SysLogHandler(address='/dev/log')
syslog.setLevel(logging.DEBUG)
syslog.setFormatter(Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S'))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(syslog)


def policy_enumerate():

    response1 = iam.list_attached_role_policies(RoleName=role)
    response2 = iam.list_role_policies(RoleName=role)

    print('\nThe following permissions belong to the role {}: \n'.format(role))

    for attached_policy in response1['AttachedPolicies']:
        role_policy1 = iamres.Policy(attached_policy['PolicyArn'])
        #print('\n' + role_policy1.arn.split('/')[2])

        policy = iam.get_policy(PolicyArn=role_policy1.arn)
        policy_version = iam.get_policy_version(PolicyArn=role_policy1.arn, VersionId=policy['Policy']['DefaultVersionId'])
        # policy_statement = policy_version['PolicyVersion']['Document']['Statement']
        # print(json.dumps(policy_statement))

        values = []

        for statement in policy_version['PolicyVersion']['Document']['Statement']:
            resource = statement['Resource']
            effect = statement['Effect']

            for action in statement['Action']:
                values.append([action.split(':')[0], action.split(':')[1], resource, effect, role_policy1.arn.split('/')[2]])

    for policy_name in response2['PolicyNames']:
        role_policy2 = iamres.RolePolicy(role, policy_name)
        # print('\n' + role_policy2.name)
        policy_statement = role_policy2.policy_document['Statement']
        # print(policy_statement)

        values2 = []

        for pol_stat in policy_statement:
            resource = pol_stat['Resource']
            effect = pol_stat['Effect']
            for action in pol_stat['Action']:
                values2.append([action.split(':')[0], action.split(':')[1], resource, effect, role_policy2.name])

    values = values + values2
    values.sort()

    x = PrettyTable()

    x.field_names = ["Service", "Action", "Resource", "Effect", "Policy name"]
    x.align["Service"] = "l"
    x.align["Action"] = "l"
    x.align["Policy name"] = "l"

    for value in values:
        #print (str(value)+"\n")
        value_parsed_json = ""
        value_parsed_json = json.load(value)
        if "Service" == str(args['regex-filter-type']):
            if re.match(args['regex-filter'], value_parsed_json[0]):
                x.add_row(value)
        # Repeat the above logic for each column
        #...
        #...
                #print(x)


# def try_resources():
#
#     lambda_client = boto3.client('lambda', region_name='us-west-2')
#
#     try:
#         print('\nPrinting the functions in Lambda:')
#         print(lambda_client.list_functions())
#     except Exception as e:
#         print('Error: {}'.format(e))
#
#     role_arn_mod = ':'.join(role_arn.split(':')[:5]) + ':role/' + role_arn.split('/')[1]
#
#     with open('lambda.zip', 'rb') as f:
#       zipped_code = f.read()
#
#     try:
#         print('\nCreating a new function in Lambda:')
#         lambda_client.create_function(
#           FunctionName='myLambdaFunction',
#           Runtime='python2.7',
#           Role=role_arn_mod,
#           Handler='main.handler',
#           Code=dict(ZipFile=zipped_code)
#         )
#     except Exception as e:
#         print('Error: {}'.format(e))
#
#     ec2 = boto3.resource('ec2', region_name='us-west-2')
#     ami_ids = []
#     for instance in ec2.instances.all():
#         ami_ids.append(instance.image_id)
#     try:
#         ec2.create_instances(ImageId=ami_ids[1], MinCount=1, MaxCount=5)
#     except Exception as e:
#         print('Error: {}'.format(e))

if __name__ == '__main__':
    arn = ARN()
    # services = arn.service.choices()


    iam = boto3.client('iam')
    iamres = boto3.resource('iam')
    r = requests.get('http://169.254.169.254/latest/meta-data/iam/info')
    role_arn = json.loads(r.text)['InstanceProfileArn']
    role = role_arn.split('/')[1]

    policy_enumerate()
    # try_resources()
