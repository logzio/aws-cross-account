import base64
import json
import logging
import gzip
import binascii

from shipper.shipper import LogzioShipper

# set logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_TYPE = 'aws-cross-account'


def _extract_record_data(data):
    try:
        # decompress the payload if it looks gzippy
        decoded = base64.b64decode(data)
        if binascii.hexlify(decoded[0:2]) == b'1f8b':
            return gzip.decompress(decoded)
        else:
            return decoded
    except TypeError as e:
        logger.error(f'Failed to decode record data: {e}')
        raise


def get_type_from_log_group(log_group):
    log_group_array = log_group.split("/")
    service_index = 2
    try:
        service_name = log_group_array[service_index]
        if service_name.lower() == 'event' or service_name == 'events':
            return log_group_array[service_index + 1]
    except Exception as e:
        logger.warning(f'Could not find the type for log group: {log_group}. Got exception: {e}')
        logger.warning(f'Using default type {DEFAULT_TYPE} for this log')
        return DEFAULT_TYPE
    return log_group_array[service_index]


def _extract_logs_from_data(data):
    data_dict = json.loads(data)
    logs = []
    for event in data_dict['logEvents']:
        new_log = data_dict.copy()
        new_log.pop("logEvents")
        parsed_event = _json_string_to_dict(event)
        if 'message' in parsed_event and isinstance(parsed_event['message'], dict):
            new_log.update(parsed_event['message'])
            parsed_event.pop('message')
        new_log.update(parsed_event)
        new_log["@timestamp"] = new_log["timestamp"]
        new_log.pop("timestamp")
        new_log["id"] = str(new_log["id"])
        if 'logGroup' in new_log:
            new_log["type"] = get_type_from_log_group(new_log["logGroup"])
        else:
            logger.warning(f'Could not find logGroup field in log. Setting log with default type {DEFAULT_TYPE}')
            new_log["type"] = DEFAULT_TYPE
        logs.append(new_log)
    return logs


def _json_string_to_dict(service_json):
    parsed = {}
    if isinstance(service_json, dict):
        parsed = service_json.copy()
    else:
        parsed = json.loads(service_json)
    for key, value in parsed.items():
        if isinstance(value, str):
            try:
                parsed[key] = json.loads(value)
            except Exception:
                parsed[key] = value
    return parsed


def lambda_handler(event, context):
    logger.info(f'Received {len(event["Records"])} raw Kinesis records.')
    shipper = LogzioShipper()
    for record in event['Records']:
        data = _extract_record_data(record['kinesis']['data'])
        logs = _extract_logs_from_data(data)
        for log in logs:
            shipper.add(log)
    shipper.flush()
