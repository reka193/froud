# froud

[![Maintainability](https://api.codeclimate.com/v1/badges/9244f8bb4c71e85e3851/maintainability)](https://codeclimate.com/github/reka193/froud/maintainability)

Penetration testing toolset for the Amazon cloud.

## Quick installation

```
  $ pip install -r requirements.txt
```

## Additional configuration for resource.py 
```
1. Create file: ~/.skew
2. Edit file's content:
accounts:
  "ACCOUNT_ID_NUMBER":
    profile: default
```
Find example file in the repo: .skew

## Config file
If conf.json is present, the scripts will use the credentials and configuration data from this config file.
The SQS parameters only need to be set for the fuzzer.py script.

If the config file is not present, the scripts will use the shared credentials and configuration files from ~/.aws/credentials and ~/.aws/config

## Usage
```
  python chosen_file.py
example:
  python rolepolicies.py
  python dynamodb.py -t <TableName>
```
  
 ## Tools
 
 ### rolepolicies.py
 Lists inline and managed policies attached to the role of the instance profile.
 ### resource.py
 Lists available resources with the given credentials.
 ### dynamodb.py
 Scans the given DynamoDB table, saving the results locally or uploading them publicly to an S3 bucket.
 ### sqs.py
 Scans the given SQS queue, saving the results locally or uploading them publicly to an S3 bucket.
 ### cloudwatch.py
 Scans the available Cloudwatch logs, saving the results locally or uploading them publicly to an S3 bucket.
 ### fuzzer.py
 Sends fuzz messages to the given SQS queue.
 
 More information about usage can be found using:
 ```
 python chosen_file.py -h
 ```
