from __future__ import print_function
import json
import re
import boto3
from kitty.model import String, Delimiter
import sys
import ast


def init():
    config_parsing_was_successfull = None
    region_name = ""
    aws_access_key_id = ""
    aws_secret_access_key = ""
    upload_endpoint_url = ""
    fuzz_endpoint_url = ""
    sqs_message = {}

    # If the config file cannot be loaded then boto3 will use its cached data because the global variables contain nonsense ("N/A")
    config_parsing_was_successfull, region_name, aws_access_key_id, aws_secret_access_key, fuzz_endpoint_url, \
    sqs_message = load_config_json("conf.json")

    if not config_parsing_was_successfull:
        region_name = "N/A"
        aws_access_key_id = "N/A"
        aws_secret_access_key = "N/A"
        fuzz_endpoint_url = "N/A"
        sqs_message = {}

    sqs_client = boto3.resource('sqs',
                                endpoint_url=fuzz_endpoint_url or None,
                                region_name=region_name or None,
                                aws_access_key_id=aws_access_key_id or None,
                                aws_secret_access_key=aws_secret_access_key or None)

    return sqs_client, sqs_message


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
        region_name = config_json["region_name"]
    except Exception as e:
        print("Error parsing 'region_name' from the config file: {}".format(e))
        sys.exit()

    try:
        aws_access_key_id = config_json["aws_access_key_id"]
    except Exception as e:
        print("Error parsing 'aws_access_key_id' from the config file: {}".format(e))
        sys.exit()

    try:
        aws_secret_access_key = config_json["aws_secret_access_key"]
    except Exception as e:
        print("Error parsing 'aws_secret_access_key' from the config file: {}".format(e))
        sys.exit()

    try:
        fuzz_endpoint_url = config_json["fuzz_endpoint_url"]
    except Exception as e:
        print("Error parsing 'fuzz_endpoint_url' from the config file: {}".format(e))
        sys.exit()

    try:
        sqs_message = config_json["sqs_message"][0]
    except Exception as e:
        print("Error parsing 'sqs_message' from the config file: {}".format(e))
        sys.exit()

    return True, region_name, aws_access_key_id, aws_secret_access_key, fuzz_endpoint_url, sqs_message


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


def fuzz(sqs, queue_name, sqs_message):

    queue = sqs.create_queue(QueueName=queue_name)

    print('Generate messages into the {} queue'.format(queue_name))
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
    sqs, sqs_message = init()

    print("\n\n")
    print("Fuzzing...\n\n")
    fuzz(sqs, 'mrupdater-notifs', sqs_message)
