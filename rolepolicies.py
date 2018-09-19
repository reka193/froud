import boto3
import requests
import json
from prettytable import PrettyTable
import argparse
import os
from argparse import RawTextHelpFormatter
import re
import sys


def init():
    init_keys()

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

    values_to_print = []

    for value in values:
        match = True

        if args['service'] and re.match(args['service'], value[0]):
            values_to_print.append(value)
            match = False
        if match and args['action'] and re.match(args['action'], value[1]):
            values_to_print.append(value)
            match = False
        if match and args['resource'] and re.match(args['resource'], value[2]):
            values_to_print.append(value)
            match = False
        if match and args['effect'] and re.match(args['effect'], value[3]):
            values_to_print.append(value)
            match = False
        if match and args['policyname'] and re.match(args['policyname'], value[4]):
            values_to_print.append(value)
            match = False

    if match:
        values_to_print = values

    print_table(values_to_print, ["Service", "Action", "Resource", "Effect", "Policy name"])


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

    args = init()
    policy_enumerate(args)
