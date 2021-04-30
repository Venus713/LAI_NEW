import json
from decimal import Decimal

from facebook_business.adobjects.campaign import Campaign

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.batch import Batch
from .helpers import (
    get_campaign,
    accounts_get_selectable_events,
    get_account_pixels,
    get_account_mobile_apps,
    fb_get_active_audiences,
    fb_make_lookalikes
)

pk = 'Campaign'

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()


def get_selectable_events_handler(event, context):
    '''
    Lambda handler to get accounts_get_selectable_events
    '''
    lambda_name = 'get_selectable_events'
    logger.info(
        'Received event in get_selectable_events: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')

    data = accounts_get_selectable_events(fb_account_id)

    return response.handler_response(
        200, data, 'Successfully get the accounts_get_selectable_events')


def account_pixels_handler(event, context):
    '''
    Lambda handler to get the account_pixels
    '''
    lambda_name: str = 'account_pixels'
    logger.info(
        f'Received event in account_pixels: {json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')

    data = get_account_pixels(fb_account_id)

    return response.handler_response(
        200, data, 'Success in account_pixels')


def account_mobile_apps_handler(event, context):
    '''
    Lambda handler to get the account_mobile_apps
    '''
    lambda_name: str = 'account_mobile_apps'
    logger.info(
        'Received event in account_mobile_apps: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')

    data = get_account_mobile_apps(fb_account_id)
    return response.handler_response(
        200, data, 'Success in account_mobile_apps')


def get_page_list_handler(event, context):
    '''
    Lambda handler to get the get_page_list
    '''
    lambda_name: str = 'get_page_list'
    logger.info(
        'Received event in get_page_list: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    data = fb_api.get_page_list(fb_access_token)
    return response.handler_response(
        200, data, 'Success in get_page_list')


def active_audiences_handler(event, context):
    '''
    Lambda handler to get the active_audiences
    '''
    lambda_name: str = 'active_audiences'
    logger.info(
        'Received event in active_audiences: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')

    data = fb_get_active_audiences(fb_account_id)
    return response.handler_response(
        200, data, 'Success in active_audiences')


def fb_make_lookalikes_handler(event, context):
    '''
    Lambda handler to get the fb_make_lookalikes
    '''
    lambda_name: str = 'fb_make_lookalikes'
    logger.info(
        'Received event in fb_make_lookalikes: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')

    body_required_field = ('audience_id', 'country',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    data = fb_make_lookalikes(
        fb_account_id, res['audience_id'], res['country'])
    return response.handler_response(
        200, data, 'Success in fb_make_lookalikes')


def create_campain(event, context):
    '''
    Lambda handler to create the campaigns
    '''
    lambda_name: str = 'create_campaign'
    logger.info(
        f'Received event in create_campaign: {json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')



def campaign_list(event, context):
    '''
    Lambda handler to get campaign_list
    '''
    lambda_name: str = 'campaign_list'
    logger.info(
        f'Received event in campaign_list: {json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_account_id = user_info.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')

    api = fb_api.get_facebook_api(fb_access_token)

    campaign_query_item = {
        'fb_account_id': fb_account_id
    }
    campaign_info = client.query_item(pk, campaign_query_item)

    campaign_rows = []

    for cp in campaign_info:
        if cp.get('campaign_name'):
            campaign_rows.append(cp)

    results = []
    with Batch(api, results) as batcher:
        for cp_row in campaign_rows:
            campaign_id = str(cp_row.get('campaign_id'))
            campaign = Campaign(campaign_id, api=api)
            campaign.api_get(
                fields=[
                    'objective', 'effective_status', 'daily_budget', 'name'
                ],
                batch=batcher.get_batch()
            )

    row_by_id = {row[0]: row for row in campaign_rows}

    campaign_data = []
    for result in results:
        campaign_id = result.get('campaign_id')
        if 'daily_budget' not in result.keys():
            logger.info(f"No daily budget found for: {campaign_id} ")
            result['daily_budget'] = 0

        item = {'budget': Decimal(result['daily_budget'])}
        client.update_item(pk, campaign_id, item)
        campaign = Campaign(campaign_id, api=api)
        campaign.update(result)
        try:
            campaign_data.append(get_campaign(
                api,
                fb_account_id,
                campaign['id'],
                preloaded_campaign_object=campaign,
                preloaded_db_row=row_by_id[int(campaign['id'])],
                skip_extras=True))
        except Exception as e:
            logger.error(f'errro in campaign_list: {e}')

    available_conversion_events = accounts_get_selectable_events(fb_account_id)

    for c in campaign_data:
        c['available_events'] = available_conversion_events
        cp = client.get_item('async_campaign_changes', c['campaign_id'])
        if cp:
            c['in_progress'] = True

    return response.handler_response(
        200, campaign_data, 'Successfully get the campaign_list')


def delete_campaign(event, context):
    '''
    Lambda handler to delete the campaigns
    '''
    lambda_name: str = 'delete_campaign'
    logger.info(
        'Received event in delete_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    campaign_id = event['pathParameters']['id']

    api = fb_api.get_facebook_api(fb_access_token)
    campaign = Campaign(campaign_id, api=api)
    campaign.api_update(params={'status': 'DELETED'})
    client.delete_item(pk, campaign_id)
    campaign_contains_ads = client.query_item(
        'Campaign_Ad',
        {'campaign_id': campaign_id}
    )
    for c in campaign_contains_ads:
        client.delete_item('Campaign_Ad', 'campaign_id', c.get('campaign_id'))

    return response.handler_response(
        200, None, 'Successfully deleted')
