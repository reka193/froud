import boto3
import requests
import json
from prettytable import PrettyTable
import argparse
import ast
from argparse import RawTextHelpFormatter

import logging
from logging.handlers import SysLogHandler
from logging import Formatter
import re


def init():
    parser = argparse.ArgumentParser(
        description='[*] List of policies attached to the role of the current user.\n'
                    '[*] The results can be filtered by any of the returned attributes using regular expressions.\n'
                    '[*] Returned policy attributes:\n'
                    '   [+] Service: The name of the service.\n'
                    '   [+] Action: Describes the specific action(s) that will be allowed or denied.\n'
                    '   [+] Resource: Specifies the object or objects that the statement covers.\n'
                    '   [+] Effect: Specifies whether the statement results in an allow or an explicit deny.\n'
                    '   [+] Policy name: The name of the AWS managed or inline policy.'
                    ' \n\nExample: \n    python rolepolicies.py -s ec2 -a Desc.* -r \* -e Allow -p ^Amazon',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-s', '--service', help='Regular expression filter for the Service column.', required=False)
    parser.add_argument('-a', '--action', help='Regular expression filter for the Action column.', required=False)
    parser.add_argument('-r', '--resource', help='Regular expression filter for the Resource column.',
                        required=False)
    parser.add_argument('-e', '--effect', help='Regular expression filter for the Effect column.', required=False)
    parser.add_argument('-p', '--policyname', help='Regular expression filter for the Policy name column.',
                        required=False)
    args = vars(parser.parse_args())

    return args


def policy_enumerate(args):
    iam = boto3.client('iam')
    iamres = boto3.resource('iam')
    r = requests.get('http://169.254.169.254/latest/meta-data/iam/info')
    role_arn = json.loads(r.text)['InstanceProfileArn']
    role = role_arn.split('/')[1]

    response1 = iam.list_attached_role_policies(RoleName=role)
    response2 = iam.list_role_policies(RoleName=role)

    print('\nThe following permissions belong to the role {}: \n'.format(role))

    for attached_policy in response1['AttachedPolicies']:
        role_policy1 = iamres.Policy(attached_policy['PolicyArn'])

        policy = iam.get_policy(PolicyArn=role_policy1.arn)
        policy_version = iam.get_policy_version(PolicyArn=role_policy1.arn,
                                                VersionId=policy['Policy']['DefaultVersionId'])

        values = []

        for statement in policy_version['PolicyVersion']['Document']['Statement']:
            resource = statement['Resource']
            effect = statement['Effect']

            for action in statement['Action']:
                values.append(
                    [action.split(':')[0], action.split(':')[1], resource, effect, role_policy1.arn.split('/')[2]])

    for policy_name in response2['PolicyNames']:
        role_policy2 = iamres.RolePolicy(role, policy_name)
        policy_statement = role_policy2.policy_document['Statement']

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
        if args['service'] is None and args['action'] is None and args['resource'] is None and \
                args['effect'] is None and args['policyname'] is None:
            x.add_row(value)
            continue
        all_matched = True
        value_list = str(value).replace("u'", "'")
        value_list = ast.literal_eval(value_list)
        try:
            if not re.match(args['service'], value_list[0]):
                all_matched = False
        except:
            pass
        try:
            if not re.match(args['action'], value_list[1]):
                all_matched = False
        except:
            pass
        try:
            if not re.match(args['resource'], value_list[2]):
                all_matched = False
        except:
            pass
        try:
            if not re.match(args['effect'], value_list[3]):
                all_matched = False
        except:
            pass
        try:
            if not re.match(args['policyname'], value_list[4]):
                all_matched = False
        except:
            pass

        if all_matched:
            x.add_row(value)

    print(x)


if __name__ == '__main__':

    args = init()
    policy_enumerate(args)
