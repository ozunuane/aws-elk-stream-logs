import base64
import gzip
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
HOST = os.getenv('LOGSTASH_HOST')
PORT = os.getenv('LOGSTASH_PORT')

import socket

#if you want to add some metadata
metadata = {}


def lambda_handler(event, context):
 # Check prerequisites

 # Attach Logstash TCP Socket

 s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

 s.connect((HOST, PORT))

 # Add the context to meta
 metadata["aws"] = {}
 metadata["aws"]["function_name"] = context.function_name
 metadata["aws"]["function_version"] = context.function_version
 metadata["aws"]["invoked_function_arn"] = context.invoked_function_arn
 metadata["aws"]["memory_limit_in_mb"] = context.memory_limit_in_mb

 try:
 logs = awslogs_handler(s, event)

 for log in logs:
 send_entry(s, log)

 except Exception as e:
 # Logs through the socket the error
 err_message = 'Error parsing the object. Exception: {}'.format(str(e))
 send_entry(s, err_message)
 raise e
 finally:
 s.close()


# Handle CloudWatch events and logs
def awslogs_handler(s, event):
 # Get logs
 data = gzip.decompress(base64.b64decode(event["awslogs"]["data"]))
 logs = json.loads(data)

 structured_logs = []

 # Send lines to Logstash
 for log in logs["logEvents"]:
 # Create structured object and send it
 structured_line = merge_dicts(log, {
 "aws": {
 "awslogs": {
 "logGroup": logs["logGroup"],
 "logStream": logs["logStream"],
 "owner": logs["owner"]
 }
 }
 })
 structured_logs.append(structured_line)

 return structured_logs


def send_entry(s, log_entry):
 # The log_entry can only be a string or a dict
 if isinstance(log_entry, str):
 log_entry = {"message": log_entry}
 elif not isinstance(log_entry, dict):
 raise Exception(
 "Cannot send the entry as it must be either a string or a dict. Provided entry: " + str(log_entry))

 # Merge with metadata
 log_entry = merge_dicts(log_entry, metadata)

 # Send to Logstash
 str_entry = json.dumps(log_entry)
 result = s.send((str_entry + "\n").encode("UTF-8"))
 # result = s.send(log_entry)


def merge_dicts(a, b, path=None):
 if path is None: path = []
 for key in b:
 if key in a:
 if isinstance(a[key], dict) and isinstance(b[key], dict):
 merge_dicts(a[key], b[key], path + [str(key)])
 elif a[key] == b[key]:
 pass # same leaf value
 else:
 raise Exception(
 'Conflict while merging metadatas and the log entry at %s' % '.'.join(path + [str(key)]))
 else:
 a[key] = b[key]
 return a