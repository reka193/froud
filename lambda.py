import boto3
import json
import requests
import argparse
import sys
from argparse import RawTextHelpFormatter
from prettytable import PrettyTable


parser = argparse.ArgumentParser(description=' !!! DESCRIPTION GOES HERE !!! \n\nExample: \n    python lambda.py -f theNameOfTheFile', formatter_class=RawTextHelpFormatter)
parser.add_argument('-f', '--fileName', help='The name of the file.', required=True)
parser.add_argument('-func', '--functionName', help='The name you want to assign to the function you are uploading.', required=True)
parser.add_argument('-r', '--runTime', help='The runtime environment for the Lambda function you are uploading.', required=True)
args = vars(parser.parse_args())


def load_config_json(config_json_filename):
    try:
        with open(config_json_filename) as config_file_handler:
            try:
                config_json = json.load(config_file_handler)
            except Exception as e:
                print("Error parsing config file: {}".format(e))
                sys.exit()
    except Exception as e:
        print("Error opening file: {}".format(e))
        return False

    try:
        region_name_for_logs = config_json["region_name_for_logs"]
    except Exception as e:
        print("Error parsing 'region_name_for_logs' from the config file: {}".format(e))
        sys.exit()

    return True, region_name_for_logs


def try_resources():

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables contain nonesens ("N/A")
    config_parsing_was_successful, region_name_for_logs = load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    lambda_client = boto3.client('lambda', region_name=region_name_for_logs)
    r = requests.get('http://169.254.169.254/latest/meta-data/iam/info')
    role_arn = json.loads(r.text)['InstanceProfileArn']

    try:
        print('\nThe existing functions in Lambda:')
        functions = lambda_client.list_functions()
        values = []

        for func in functions['Functions']:
            values.append([func['FunctionName'], func['Runtime'], func['Description']])
    except Exception as e:
        print('Error: {}'.format(e))

    role_arn_mod = ':'.join(role_arn.split(':')[:5]) + ':role/' + role_arn.split('/')[1]

    try:
        with open(args['fileName'], 'rb') as f:
            zipped_code = f.read()
    except Exception as e:
        print('Commandline specified file could not be loaded: {}'.format(e))

    try:
        print('\nCreating a new function in Lambda:')
        lambda_client.create_function(
          FunctionName=args['functionName'],
          Runtime=args['runTime'],
          Role=role_arn_mod,
          Handler='main.handler',
          Code=dict(ZipFile=zipped_code)
        )
    except Exception as e:
        print('Error: {}'.format(e))

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
    values = try_resources()
    print_table(values, ['FunctionName', 'Runtime', 'Description'])


if __name__ == '__main__':
    main()
