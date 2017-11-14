import boto3
import json
import os
import sys

sys.path.append(f"{os.environ['LAMBDA_TASK_ROOT']}/lib")

import cr_response
import stack_manage
import lambda_invoker

create_stack_success_states = ['CREATE_COMPLETE']
update_stack_success_states = ['UPDATE_COMPLETE']
delete_stack_success_states = ['DELETE_COMPLETE']

create_stack_failure_states = ['CREATE_FAILED',
                               'DELETE_FAILED',
                               'UPDATE_FAILED',
                               'ROLLBACK_FAILED',
                               'DELETE_COMPLETE',
                               'ROLLBACK_COMPLETE']
update_stack_failure_states = ['CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED', 'ROLLBACK_COMPLETE']
delete_stack_failure_states = ['DELETE_FAILED']


def create_stack(payload):
    # compile stack parameters
    stack_params = {}
    for key, value in payload['ResourceProperties'].items():
        if key.startswith('StackParam_'):
            param_key = key.replace('StackParam_', '')
            param_value = value
            stack_params[param_key] = param_value
    
    # instantiate and use management handler
    manage = stack_manage.StackManagement()
    
    on_failure = 'DELETE'
    if 'OnFailure' in payload['ResourceProperties']:
        on_failure = payload['ResourceProperties']['OnFailure']
        
    stack_id = manage.create(
        payload['ResourceProperties']['Region'],
        payload['ResourceProperties']['StackName'],
        payload['ResourceProperties']['TemplateUrl'],
        stack_params,
        payload['ResourceProperties']['Capabilities'].split(','),
        on_failure
    )
    
    return stack_id


def update_stack(payload):
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    metadata_key = payload['ResourceProperties']['MetadataKey']
    return {"PhysicalResourceId": f"arn:aws:metadata:{account_id}:metadata/{metadata_key}"}


def delete_stack(payload):
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    metadata_key = payload['ResourceProperties']['MetadataKey']
    return {"PhysicalResourceId": f"arn:aws:metadata:{account_id}:metadata/{metadata_key}"}


def wait_stack_states(success_states, failure_states, lambda_payload, lambda_context):
    """
    Wait for stack states, either be it success or failure. If none of the states
    appear and lambda is running out of time, it will be re-invoked with lambda_payload
    parameters
    :param lambda_context:
    :param stack_id:
    :param success_states:
    :param failure_states:
    :param lambda_payload:
    :return:
    """
    manage = stack_manage.StackManagement()
    result = manage.wait_stack_status(
        lambda_payload['ResourceProperties']['Region'],
        lambda_payload['PhysicalResourceId'],
        success_states,
        failure_states,
        lambda_context
    )
    
    # in this case we need to restart lambda execution
    if result is None:
        invoke = lambda_invoker.LambdaInvoker()
        invoke.invoke(lambda_payload)
    else:
        # one of the states is reached, and reply should be sent back to cloud formation
        cfn_response = cr_response.CustomResourceResponse(lambda_payload)
        cfn_response.response['PhysicalResourceId'] = lambda_payload['PhysicalResourceId']
        cfn_response.response['Status'] = result.status
        cfn_response.response['Reason'] = result.reason
        cfn_response.response['StackId'] = lambda_payload['StackId']
        cfn_response.respond()


def lambda_handler(payload, context):
    # if lambda invoked to wait for stack status
    print(f"Received event:{json.dumps(payload)}")
    if ('WaitComplete' in payload) and (payload['WaitComplete']):
        print("Waiting for stack status...")
        if payload['RequestType'] == 'Create':
            wait_stack_states(
                create_stack_success_states,
                create_stack_failure_states,
                payload,
                context
            )
        
        elif payload['RequestType'] == 'Update':
            wait_stack_states(
                payload['PhysicalResourceId'],
                create_stack_success_states,
                create_stack_failure_states,
                payload,
                context
            )
        
        elif payload['RequestType'] == 'Delete':
            wait_stack_states(
                payload['PhysicalResourceId'],
                create_stack_success_states,
                create_stack_failure_states,
                payload,
                context
            )
    
    # lambda was invoked directly by cf
    else:
        # depending on request type different handler is called
        print("Executing stack CRUD...")
        stack_id = None
        try:
            if payload['RequestType'] == 'Create':
                stack_id = create_stack(payload)
            elif payload['RequestType'] == 'Update':
                stack_id = update_stack(payload)
            elif payload['RequestType'] == 'Delete':
                stack_id = delete_stack(payload)
            
            # add marker to wait for execution and exit
            payload['PhysicalResourceId'] = stack_id
            payload['WaitComplete'] = True
            invoker = lambda_invoker.LambdaInvoker()
            invoker.invoke(payload)
        
        except Exception as e:
            print(f"Exception:{e}\n{str(e)}")
            print(e.__traceback__)
            cfn_response = cr_response.CustomResourceResponse(payload)
            if 'PhysicalResourceId' in payload:
                cfn_response.response['PhysicalResourceId'] = payload['PhysicalResourceId']
            cfn_response.response['Status'] = 'FAILURE'
            cfn_response.response['Reason'] = str(e)
            cfn_response.respond()
            raise e
