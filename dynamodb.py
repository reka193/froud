import boto3

dinamo = boto3.client('dynamodb', region_name='us-west-2')
table_names = dinamo.list_tables()['TableNames']
for table in table_names:
    print(table)
    attribute_def = dinamo.describe_table(TableName=table)['Table']['AttributeDefinitions']
    print(attribute_def)
    scan = dinamo.scan(TableName=table)
    print(scan)
    print ('\n')
