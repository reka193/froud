from __future__ import print_function
import json
import re
import boto3
from kitty.model import String, Delimiter
import ast
import common
import sys


def init():

    # If the config file cannot be loaded then boto3 will use the aws credentials file
    config_success, data = common.load_config_json("conf.json", sqs=True)

    if not config_success:
        aws_access_key_id = "N/A"
        aws_secret_access_key = "N/A"
        aws_session_token = "N/A"
        region_name = "N/A"
        fuzz_endpoint_url = ""
        message_to_fuzz = {}

    else:
        aws_access_key_id, aws_secret_access_key, aws_session_token, region_name, fuzz_endpoint_url, message_to_fuzz = data

    sqs_client = boto3.resource('sqs',
                                aws_access_key_id=aws_access_key_id or None,
                                aws_secret_access_key=aws_secret_access_key or None,
                                aws_session_token=aws_session_token or None,
                                region_name=region_name or None,
                                endpoint_url=fuzz_endpoint_url or None)

    return sqs_client, message_to_fuzz


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


def generate_sqs_message_mutations(sqs_message):
    sqs_message = str(sqs_message).replace("u'", "'")
    sqs_message = str(sqs_message).replace("'", "\"")
    sqs_message = ast.literal_eval(sqs_message)
    sqs_msg = sqs_message
    out_msg = dict()
    for key, value in sqs_msg.items():
        if isinstance(value, str):
            out_msg["#{}#".format(key)] = "#{}#".format(value)
        else:
            out_msg[key] = value
    return create_fuzz_messages(json.dumps(out_msg))


def fuzz(sqs_client, queue_name, sqs_message):

    try:
        queue = sqs_client.create_queue(QueueName=queue_name)

    except Exception as e:
        print(e)
        sys.exit()

    print('Generate messages for the queue {}'.format(queue_name))
    messages = generate_sqs_message_mutations(sqs_message)
    counter = 0
    for msg in messages:
        try:
            queue.send_message(MessageBody=msg)
            counter += 1
            print("Fuzzing expression #" + str(counter) + ": " + str(msg[:40]) + "  ...  " + str(msg[-40:]))
        except:
            print('Failed message: {}'.format(msg))


if __name__ == "__main__":
    sqs, message = init()

    print("\n\n")
    print("Fuzzing...\n\n")
    fuzz(sqs, 'mrupdater-notifs', message)
