import json

from facebook_business.adobjects.adaccount import AdAccount

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from .helpers import get_fb_insights_actions_w_data

pk = 'FB_Account'

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()


def get_account_list_handler(event, context):
    '''
    Lambda handler to get account_list
    '''
    lambda_name = 'get_account_list'
    logger.info(
        'Received event in get_account_list: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'email',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp.get('email')

    account_list = []

    results = client.query_item(pk, {
        'user_email': email,
        'account_type': 'facebook'
    })

    for result in results:
        account_info = {
            'name': result.get('name'),
            'id': result.get('fb_account_id'),
            'status': result.get('status'),
            'budget': result.get('average_daily_budget'),
            'conversion_event': result.get('conversion_event'),
        }
        account_list.append(account_info)

    return response.handler_response(
        200,
        account_list,
        'Success'
    )


def get_fb_insights_actions_w_data_handler(event, context):
    '''
    Lambda handler to get fb_insights_actions_w_data
    '''
    lambda_name = 'get_fb_insights_actions_w_data'
    logger.info(
        'Received event in get_fb_insights_actions_w_data: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'events_list'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    events_list = resp.get('events_list')

    fb_api.get_facebook_api(fb_access_token)
    acc = AdAccount(f'act_{fb_account_id}')
    result = get_fb_insights_actions_w_data(fb_account_id, acc, events_list)
    return response.handler_response(
        200,
        result,
        'Success'
    )


def update_account_conversion_event_handler(event, context):
    '''
    Lambda handler to update account_conversion_event
    '''
    lambda_name = 'update_account_conversion_event'
    logger.info(
        'Received event in update_account_conversion_event: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id', 'conversation_event',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    conversation_event = resp.get('conversation_event')
    try:
        client.update_item(pk, fb_account_id + '-' + user_id, {
            'conversation_event': conversation_event
        })
    except Exception as e:
        logger.exception(f'Exception in update_account_conversion_event: {e}')
        return response.handler_response(
            400,
            None,
            'Failed: Raised an Exception.'
        )

    return response.handler_response(
        200,
        None,
        'Successfully updated'
    )


def update_account_status_handler(event, context):
    '''
    Lambda handler to update account_status
    '''
    lambda_name = 'update_account_status'
    logger.info(
        'Received event in update_account_status: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id', 'status',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    status = resp.get('status')

    try:
        client.update_item(pk, fb_account_id + '-' + user_id, {
            'status': eval(status)
        })

        if eval(status) is False:
            campaings = client.query_item('Campaign', {
                'fb_account_id': fb_account_id
            })
            for campaign in campaings:
                campaing_id = campaign.pop('sk')
                campaign.pop('pk')
                campaign['status'] = 'PAUSED'
                campaign['auto_expand'] = False
                campaign['ad_optimizer'] = False
                campaign['expand'] = False
                campaign['creative_optimization'] = False
                client.update_item(
                    'Campaign',
                    campaing_id,
                    campaign
                )
    except Exception as e:
        logger.exception(f'Exception in update_account_status: {e}')
        return response.handler_response(
            400,
            None,
            'Raised an Exception'
        )
    return response.handler_response(
        200,
        None,
        'Successfully updated'
    )
