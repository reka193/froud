from __future__ import print_function
import json
import re
import boto3
from kitty.model import String, Delimiter


def create_fuzz_messages(default_message, size=None):
    """Creates fuzzy messages by the controller's default message
    by changing the #value# formatted parts in it.

    :param string default_message: the controller's default_message
    :param int size: Defines the max length of the mutated string
    :return: list
    """

    def _static_fuzz_strings():
        fuzz_strings = []
        fuzz_strings.extend([s[0] for s in String("")._get_class_lib()])
        fuzz_strings.extend([d[0] for d in Delimiter("")._get_class_lib()])
        return fuzz_strings

    def _dynamic_fuzz_strings(value):
        fuzz_strings = []
        fuzz_strings.extend([s[0] for s in String(value)._get_local_lib()])
        fuzz_strings.extend([s[0] for s in Delimiter(value)._get_local_lib()])
        return fuzz_strings

    marker = "#"
    pieces = default_message.split(marker)
    static_fuzz_strings = _static_fuzz_strings()

    if not len(pieces) % 2:
        print('Not even number of marker found ({}), skipping default message: {}'.format(pieces, default_message))

    fuzzme_list = []
    prev_part_was_marker = False
    fuzzme_list.extend(pieces[1::2])
    response_list = []

    # issue tests for each fuzzme string
    for fuzzme in fuzzme_list:
        for part in re.split(r'(\W)', default_message):
            # fuzzable strings are surrounded with markers
            if part == marker:
                if prev_part_was_marker:
                    prev_part_was_marker = False
                else:
                    prev_part_was_marker = True
            # fuzz the current string
            elif prev_part_was_marker and part == fuzzme:
                for mutation in static_fuzz_strings + _dynamic_fuzz_strings(part):
                    # we have to avoid to replace the marker character in the mutated part!!!
                    marked_part = marker + part + marker
                    other_parts = [p.replace(marker, "") for p in default_message.split(marked_part)]
                    response_list.append(mutation.join(other_parts))
    return response_list


def generate_sqs_message_mutations():
    sqs_msg = {
        "timestamp": "#2018-08-01T10:57:36Z#",
        "version": 1,
        "update_type": "inc",
        "number_of_updates": 214,
        "type": "#labsupdate#",
        "location": {
            "bucket": "#s3-labs-updates-us-west-2#",
            "storage": "#s3x#",
            "key": "#1/2018/08/01/10/5634-20180801T105736Z-ip-172-31-36-118#"
        }
    }
    out_msg = dict()
    for key, value in sqs_msg.items():
        if isinstance(value, str):
            out_msg["#{}#".format(key)] = "#{}#".format(value)
        else:
            out_msg[key] = value
    return create_fuzz_messages(json.dumps(out_msg))


def fuzz(queue_name, region_name=None, aws_access_key_id=None, aws_secret_access_key=None, endpoint_url=None):
    sqs = boto3.resource('sqs',
                         endpoint_url=endpoint_url or None,
                         region_name=region_name or None,
                         aws_access_key_id=aws_access_key_id or None,
                         aws_secret_access_key=aws_secret_access_key or None)
    queue = sqs.create_queue(QueueName=queue_name)

    print('Generate messages into the {} queue'.format(queue_name))
    messages = generate_sqs_message_mutations()
    for msg in messages:
        try:
            queue.send_message(MessageBody=msg)
        except:
            print('Failed message: {}'.format(msg))


def upload_file(filename, region_name=None, aws_access_key_id=None, aws_secret_access_key=None, endpoint_url=None):
    session = boto3.Session()
    s3_client = session.client('s3',
                               endpoint_url=endpoint_url or None,
                               region_name=region_name or None,
                               aws_access_key_id=aws_access_key_id or None,
                               aws_secret_access_key=aws_secret_access_key or None)
    try:
        print("Uploading file: {}".format(filename))
        tc = boto3.s3.transfer.TransferConfig()
        t = boto3.s3.transfer.S3Transfer(client=s3_client, config=tc)
        t.upload_file(filename, 's3-labs-updates-us-west-2', '1/2018/08/01/10/5634-20180801T105736Z-ip-172-31-36-118')

    except Exception as e:
        print("Error uploading: {}".format(e))
        

if __name__ == "__main__":
    f = open('helofile', 'wb')
    upload_file('helofile', region_name='local', aws_access_key_id='asd',
                aws_secret_access_key='asd', endpoint_url='http://localhost:8000')
    fuzz('mrupdater-notifs', region_name='local', aws_access_key_id='asd', aws_secret_access_key='asd',
         endpoint_url='http://localhost:8001')
