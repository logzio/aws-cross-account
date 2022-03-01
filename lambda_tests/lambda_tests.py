import json
import unittest
import base64

import src.lambda_function as SRC


class TestLambdaFunction(unittest.TestCase):
    def test_event_from_lambda_service(self):
        with open('./lambda_logs.json', 'rb') as lambda_json:
            data = base64.b64encode(lambda_json.read())
        with open('./kinesis_event.json', 'r') as kinesis_event_file:
            event = json.load(kinesis_event_file)
        event['Records'][0]['kinesis']['data'] = data
        for record in event['Records']:
            data = SRC._extract_record_data(record['kinesis']['data'])
            logs = SRC._extract_logs_from_data(data)
        self.assertEqual(len(logs), 6)
        for log in logs:
            self.assertTrue('message' in log)
            self.assertTrue(isinstance(log['message'], str))
            self.assertEqual(log['type'], 'lambda')

    def test_event_from_cloudtrail_service(self):
        with open('./cloudtrail_logs.json', 'rb') as lambda_json:
            data = base64.b64encode(lambda_json.read())
        with open('./kinesis_event.json', 'r') as kinesis_event_file:
            event = json.load(kinesis_event_file)
        event['Records'][0]['kinesis']['data'] = data
        for record in event['Records']:
            data = SRC._extract_record_data(record['kinesis']['data'])
            logs = SRC._extract_logs_from_data(data)
        self.assertEqual(len(logs), 1)
        for log in logs:
            self.assertFalse('message' in log)
            self.assertTrue('eventVersion' in log)
            self.assertEqual(log['type'], 'cloudtrail')


if __name__ == '__main__':
    unittest.main()
