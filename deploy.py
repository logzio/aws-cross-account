#!/usr/bin/python3
import os
import subprocess
import sys
import time

import boto3
from ruamel.yaml import YAML

AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-south-1', 'ap-northeast-3',
               'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
               'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'sa-east-1']
VERSION = '0.0.1'
BUCKET_BASE = 'logzio-aws-integrations'
NAME = 'aws-cross-accounts'
AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET_KEY = os.environ['AWS_SECRET_KEY']
PATH_PREFIX = f'{NAME}/{VERSION}'
LAMBDA_KEY = f'{PATH_PREFIX}/lambda_function.zip'
SAM_MAIN_KEY = f'{PATH_PREFIX}/sam-template-main.yaml'
SAM_DESTINATION_KEY = f'{PATH_PREFIX}/sam-template-destination.yaml'


def run():
    zip_path = './lambda_function.zip'  # TODO: may need to change in the workflow
    zip_lambda_function()

    for region in AWS_REGIONS:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=region
        )
        bucket_name = f'{BUCKET_BASE}-{region}'
        # validate that the version number is correct, so we do not override an existing version:
        result = s3_client.list_objects(Bucket=bucket_name, Prefix=f'{PATH_PREFIX}')
        print(f'Result: {result}')
        if 'Contents' in result:
            print('ERROR! This version already exists. Please bump version with variable VERSION, and run the script again!')
            os.remove(zip_path)
            exit(1)
        # upload lambda function
        uploaded = upload_file(s3_client, bucket_name, LAMBDA_KEY, zip_path, region)
        if not uploaded:
            sys.exit('Error occurred while uploading lambda zip')
        os.remove(zip_path)
        # handle + upload main sam template
        uploaded = edit_and_upload_template(s3_client, bucket_name, region)
        if not uploaded:
            sys.exit('Error occurred while uploading main sam template')
        # upload destination template
        uploaded = upload_file(s3_client, bucket_name, SAM_DESTINATION_KEY,
                               './sam-templates/sam-template-destination.yaml', region)
        if not uploaded:
            sys.exit('Error occurred while uploading destination sam template')
    print('Finished uploading resources successfully!')


def upload_file(s3_client, bucket, key, file_to_upload, region):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = s3_client.upload_file(file_to_upload, bucket, key)
        except Exception as e:
            print(e)
            time.sleep(3)
        print(f'Successfully deployed {key} in region: {region}')
        return True
    return False


def zip_lambda_function():
    subprocess.call('./zip.sh')


def edit_and_upload_template(s3_client, bucket_name, region):
    try:
        base_file_path = './sam-templates/sam-template-main-default.yaml'
        file_path = './sam-templates/sam-template-main.yaml'
        yaml = YAML()
        with open(base_file_path, 'r') as template_base:
            template_yaml = yaml.load(template_base)
            template_yaml['Resources']['LogzioCrossAccountKinesisLambda']['Properties']['CodeUri']['Bucket'] = bucket_name
            template_yaml['Resources']['LogzioCrossAccountKinesisLambda']['Properties']['CodeUri']['Key'] = LAMBDA_KEY
            with open(file_path, 'w') as template:
                yaml.dump(template_yaml, template)
        uploaded = upload_file(s3_client, bucket_name, SAM_MAIN_KEY, file_path, region)
        os.remove(file_path)
        return uploaded
    except Exception as e:
        print(e)
        return False


if __name__ == '__main__':
    run()
