import sys
import os
import re

sys.path.append(f"{os.environ['LAMBDA_TASK_ROOT']}/lib")
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import cr_response
import logic


def lambda_handler(event, context):
    lambda_response = cr_response.CustomResourceResponse(event)
    cr_params = event['ResourceProperties']
    
    # Validate input
    for key in ['Source', 'Destination']:
        if key not in cr_params:
            lambda_response.respond_error(f"{key} property missing")
            return
    
    # Validate input params format
    src_param = cr_params['Source']
    dst_param = cr_params['Destination']
    src_param_match = re.match(r's3:\/\/(.*?)\/(.*)', src_param)
    dst_param_match = re.match(r's3:\/\/(.*?)\/(.*)', dst_param)
    
    if src_param_match is None or dst_param_match is None:
        lambda_response.respond_error(f"Source/Destination must be in s3://bucket/key format")
        return
    
    # get prefixes
    src_prefix = src_param_match.group(2)
    dst_prefix = dst_param_match.group(2)
    
    dst = {'Bucket': dst_param_match.group(1), 'Prefix': dst_prefix}
    
    if event['RequestType'] == 'Delete':
        logic.S3CopyLogic(context, type='clean', src=None, dst=dst).clean_destination()
        lambda_response.respond()
        return
    
    # if create request, generate physical id, both for create/update copy files
    if event['RequestType'] == 'Create':
        event['PhysicalResourceId'] = dst_param
    
    # check if source is prefix - than it is sync type
    if src_prefix.endswith('/'):
        src = {'Bucket': src_param_match.group(1), 'Prefix': src_prefix}
        logic.S3CopyLogic(context, type='sync', src=src, dst=dst).copy()
        lambda_response.respond()
    # if prefix ends with zip, we need to unpack file first
    elif src_prefix.endswith('.zip'):
        src = {'Bucket': src_param_match.group(1), 'Key': src_prefix}
        logic.S3CopyLogic(context, type='object-zip', src=src, dst=dst).copy()
        lambda_response.respond()
    # by default consider prefix as key - regular s3 object
    else:
        src = {'Bucket': src_param_match.group(1), 'Key': src_prefix}
        logic.S3CopyLogic(context, type='object', src=src, dst=dst).copy()
        lambda_response.respond()
    
    return 'OK'
