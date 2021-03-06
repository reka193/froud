import boto3
import json
import requests
import argparse
from argparse import RawTextHelpFormatter
from botocore.exceptions import ClientError
from common import load_config_json
from common import print_table


parser = argparse.ArgumentParser(description='[*] Lambda function uploader.\n'
                                             '[*] Specify the zip file to upload with the function name and runtime environment.'
                                             ' \n\nusage: \n    python lambda.py -f <FileName> -func <FunctionName> -r <RunTimeEnv>', formatter_class=RawTextHelpFormatter)

required = parser.add_argument_group('required arguments')
required.add_argument('-f', '--fileName', help='The name of the zip file containing your deployment package.', required=True)
required.add_argument('-func', '--functionName', help='The name you want to assign to the function you are uploading.', required=True)
required.add_argument('-r', '--runTime', help='The runtime environment for the Lambda function you are uploading. E.g.: python2.7', required=True)
args = vars(parser.parse_args())


def init():
    # If the config file cannot be loaded then boto3 will use its cached data because the global variables contain nonesens ("N/A")
    config_parsing_was_successful, region_name_for_logs = load_config_json("conf.json")

    if not config_parsing_was_successful:
        region_name_for_logs = "N/A"

    lambda_client = boto3.client('lambda', region_name=region_name_for_logs)
    r = requests.get('http://169.254.169.254/latest/meta-data/iam/info')
    role_arn = json.loads(r.text)['InstanceProfileArn']

    return lambda_client, role_arn


def list_functions(lambda_client):

    try:
        functions = lambda_client.list_functions()
        values = []

        for func in functions['Functions']:
            values.append([func['FunctionName'], func['Runtime'], func['Description']])
    except Exception as e:
        print('Error: {}'.format(e))

    return values


def create_run_function(lambda_client, role_arn):

    role_arn_mod = ':'.join(role_arn.split(':')[:5]) + ':role/' + role_arn.split('/')[1]

    try:
        with open(args['fileName'], 'rb') as f:
            zipped_code = f.read()
    except Exception as e:
        print('Commandline specified file could not be loaded: {}'.format(e))

    try:
        lambda_client.create_function(
          FunctionName=args['functionName'],
          Runtime=args['runTime'],
          Role=role_arn_mod,
          Handler='main.handler',
          Code={'ZipFile': zipped_code}
        )
        print('\nThe new Lambda function is uploaded.')

    except ClientError as ce:
        if ce.response['Error']['Code'] == 'InvalidParameterValueException':
            # print('Error: Could not unzip uploaded file. Please check your file, then try to upload again.')
            print(ce)

    try:
        lambda_client.invoke(FunctionName=args['functionName'])
    except Exception as e:
        print(e)


def main():
    lambda_client, role_arn = init()
    values = list_functions(lambda_client)
    print('\nThe existing functions in Lambda:')
    print_table(values, ['FunctionName', 'Runtime', 'Description'])
    create_run_function(lambda_client, role_arn)


if __name__ == '__main__':
    main()
