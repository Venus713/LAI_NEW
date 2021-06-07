import json
import datetime
from decimal import Decimal

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.stripe import Stripe
from utils.helpers import get_available_billing_plans, get_customer

from .helpers import get_active_fb_events, event_list_to_string

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()
stripe: Stripe = Stripe()


def get_adset_data_handler(event, context):
    '''
    Lambda handler to get adset_data
    '''
    lambda_name = 'get_adset_data'
    logger.info(
        'Received event in get_adset_data: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'account_id', 'campaign_name_list', 'conversion_event_name',
        'date_preset', 'attribution_window',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    account_id = resp.get('account_id')
    campaign_name_list = resp.get('campaign_name_list', [])
    conversion_event_name = resp.get('conversion_event_name')
    date_preset = resp.get('date_preset')
    attribution_window = resp.get('attribution_window')

    try:
        fb_api.get_facebook_api(fb_access_token)

        data = []

        campaign_list = campaign_name_list.split(',')
        AdAccount(f'act_{account_id}')

        adset_list = []
        for campaign_id in campaign_list:
            campaign = Campaign(campaign_id)
            adset_list.extend(
                campaign.get_ad_sets(
                    fields=[
                        'status', 'name', 'daily_budget',
                        'account_id', 'created_time'
                    ]
                )
            )

        for adset in adset_list:
            insights = adset.get_insights(
                fields=['actions', 'action_values', 'spend'],
                params={
                    'date_preset': date_preset,
                    'action_attribution_windows': attribution_window
                }
            )
            adset_data = {}

        try:
            logger.info(insights[0]['spend'])
        except Exception as e:
            logger.exception(e)
            adset_data.update({'spend': 0})
            adset_data.update({'name': adset['name']})
            adset_data.update({'status': adset['status']})
            adset_data.update({'id': adset['id']})
            adset_data.update({'account_id': adset['account_id']})
            data.append(adset_data)

        adset_data = {}
        adset_data.update({'spend': insights[0]['spend']})
        adset_data.update({'conversions': 0})
        adset_data.update({'conversion_value': 0})

        if 'actions' in insights[0]:
            actions = insights[0]['actions']

            for action in actions:
                conversions = 0
                if conversion_event_name in action['action_type']:
                    if '1d_click' in action:
                        conversions = conversions + int(action['1d_click'])
                    if '1d_view' in action:
                        conversions = conversions + int(action['1d_view'])
                    if '7d_click' in action:
                        conversions = conversions + int(action['7d_click'])
                    if '7d_view' in action:
                        conversions = conversions + int(action['7d_view'])
                    if '28d_view' in action:
                        conversions = conversions + int(action['28d_view'])
                    if '28d_click' in action:
                        conversions = conversions + int(action['28d_click'])

                    adset_data.update({'conversions': conversions})

        if 'action_values' in insights[0]:
            actions = insights[0]['action_values']

            for action in actions:
                if conversion_event_name in action['action_type']:
                    adset_data.update({'conversion_value': action['value']})

        if 'daily_budget' in adset:
            adset_data.update({'daily_budget': adset['daily_budget']})

        adset_data.update({'name': adset['name']})
        adset_data.update({'status': adset['status']})
        adset_data.update({'id': adset['id']})
        adset_data.update({'account_id': adset['account_id']})
        adset_data.update({'date_created': adset['created_time']})

        if adset_data['conversions'] > 0:
            adset_data.update(
                {
                    'cpa': str(
                        Decimal(
                            adset_data['spend'])/Decimal(
                                adset_data['conversions'])
                    )
                }
            )
        if adset_data['conversion_value'] > 0:
            adset_data.update(
                {
                    'roas': str(
                        Decimal(
                            adset_data['conversion_value'])/Decimal(
                                adset_data['spend'])
                    )
                }
            )

        data.append(adset_data)
        return response.handler_response(
            200,
            data,
            'Success'
        )
    except Exception as e:
        if 'message' in e:
            return response.handler_response(
                400,
                'None',
                f'Raised an Exception: {e}'
            )
        else:
            return response.handler_response(
                400,
                None,
                (
                    'Sorry, looks like something went wrong.'
                    ' Please message support for help.'
                )
            )


def get_changelog_handler(event, context):
    '''
    Lambda handler to get changelog on dashobard
    '''
    lambda_name = 'get_changelog'
    logger.info(
        'Received event in get_changelog: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    change_logs = client.query_item('ChangeLog', {
        'fb_account_id': fb_account_id
    })
    change_logs = sorted(
        change_logs, key=lambda i: i['changed_at'], reverse=True
    )[0:10]
    return response.handler_response(
        200,
        [{
            'description': row.get('change'),
            'date': row.get('changed_at'),
            'platform': 'facebook'
        } for row in change_logs],
        'Success'
    )


def get_notifications_handler(event, context):
    '''
    Lambda handler to get notifications on dashobard
    '''
    lambda_name = 'get_notifications'
    logger.info(
        'Received event in get_notifications: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user = client.get_item('User', user_id)
    email = user.get('email')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    change_logs = client.query_item('Trigger', {
        'fb_account_id': fb_account_id,
        'email': email,
        'trigger': True
    })
    change_logs = sorted(
        change_logs, key=lambda i: i['last_updated'], reverse=True
    )[0:10]
    return response.handler_response(
        200,
        [{
            'trigger_name': row.get('trigger_name'),
            'params': json.loads(row.get('params')),
            'date': row.get('last_updated')
        } for row in change_logs],
        'Success'
    )


def get_account_sidebar_and_dashboard_info_handler(event, context):
    '''
    Lambda handler to get account_sidebar_and_dashboard_info
    '''
    lambda_name = 'get_account_sidebar_and_dashboard_info'
    logger.info(
        'Received event in get_account_sidebar_and_dashboard_info: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    email = user_info.get('email')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    full_results = {}
    fb_account_data = client.query_item('FB_Account', {'email': email})
    full_results['user_accounts'] = fb_account_data

    # If we don't have an account id passed in by the caller,
    #  we want to default to the first account id in the list.

    fb_access_token = full_results['user_accounts'][0]['fb_access_token']
    if fb_account_id is None:
        fb_account_id = full_results['user_accounts'][0]['fb_account_id']

    # Everything else in this function is based on this one ad account, even if
    # the user has multiple ad accounts linked to their user.

    ad_account_info = client.query_item('FB_Account', {
        'fb_account_id': fb_account_id
    })
    if not ad_account_info:
        ad_account_info = [0, 0, 0, 0]

    full_results['ad_account'] = ad_account_info

    api = fb_api.get_facebook_api(fb_access_token)
    print("SDK", api.SDK_VERSION)
    print("API", api.API_VERSION)
    account = AdAccount('act_' + str(fb_account_id), api=api)
    account.api_get(fields=['currency'])
    full_results['currency'] = account['currency']

    campaign_data = client.query_item('Campaign', {
        'fb_account_id': fb_account_id
    })

    full_results['fb_campaign_list'] = [
        {
            'name': c.get('campaign_name'),
            'id': c.get('campaign_id')
        } for c in campaign_data if c.get('campaign_name')
    ]
    full_results['active_events'] = get_active_fb_events(account)

    dashboard = {}
    dashboard['optimization_info'] = [
        {
            'name': c.get('account_name'),
            'campaign_id': c.get('campaign_id'),
            'number_of_ads': c.get('number_of_ads'),
            'status': c.get('status')
        } for c in campaign_data if c.get('optimization_info')
    ]

    exp_data = [
        {
            'name': c.get('campaign_name'),
            'status': c.get('expansion_enabled'),
            'budget': c.get('budget'),
            'campaign_id': c.get('campaign_id')
        } for c in campaign_data if c.get('expansion_enabled')
    ]
    dashboard['expansion_campaigns'] = exp_data

    customer = stripe.get_customer(email)
    has_card = customer and customer['sources']['data']
    last4 = None
    if has_card:
        last4 = customer['sources']['data'][0].get("last4")

    data = {
        'name': user_info.get('credit_plan'),
        'credits': int(user_info.get('spend_credits_left', 0)),
        'error': user_info.get('charge_error'),
        'has_card': has_card,
        'last4': last4
    }
    dashboard['billing'] = data

    full_results['dashboard_info'] = dashboard

    return response.handler_response(
        200,
        full_results,
        'Success'
    )


def get_fb_insights_for_campaign_handler(event, context):
    '''
    Lambda handler to get fb_insights_for_campaign
    '''
    lambda_name = 'get_fb_insights_for_campaign'
    logger.info(
        'Received event in get_fb_insights_for_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'campaign_id', 'event'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    campaign_id = resp.get('campaign_id')
    event = resp.get('event')

    fb_api.get_facebook_api(fb_access_token)
    c = Campaign(campaign_id)

    event = event_list_to_string(event)

    try:
        if event is None:
            fb_account = client.get_item(
                'FB_Account',
                f'{fb_account_id}-{user_id}'
            )
            account_action = fb_account.get('conversion_event')
        else:
            account_action = event.upper()
        if account_action is None:
            account_action = 'LINK_CLICK'

        now = datetime.datetime.now()
        dates = [
            {
                'since': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
                'until': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            }
            for i in range(14, 0, -1)
        ]

        insights = c.get_insights(
            params={'time_ranges': dates},
            fields=['spend', 'date_start', 'impressions', 'actions']
        )

        def get_conversions(actions):
            c = [
                a for a in actions if (
                    account_action in a['action_type'].upper()
                )
            ]

            if len(c) > 0:
                return float(c[0]['value'])
            else:
                return 0

        def get_clicks(actions):
            c = [
                a for a in actions if "LINK_CLICK" in a['action_type'].upper()
            ]
            if len(c) > 0:
                return float(c[0]['value'])
            else:
                return 0

        data = [
            {
                'impressions': float(i['impressions']),
                'spend': float(i['spend']),
                'conversions': get_conversions(i['actions']),
                'clicks': get_clicks(i['actions']),
                'date': i['date_start']
            }
            for i in insights
        ]
        return response.handler_response(
            200,
            data,
            'Success'
        )
    except Exception as e:
        logger.exception(f'Raised an Exception: {e}')
        return response.handler_response(
            400,
            [],
            f'Raised an Exception: {e}'
        )


def get_fb_insights_for_account_handler(event, context):
    '''
    Lambda handler to get fb_insights_for_account
    '''
    lambda_name = 'get_fb_insights_for_account'
    logger.info(
        'Received event in get_fb_insights_for_account: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'event'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    event = resp.get('event')

    fb_api.get_facebook_api(fb_access_token)
    acc = AdAccount(f'act_{fb_account_id}')

    event = event_list_to_string(event)

    try:
        if event is None:
            fb_account = client.get_item(
                'FB_Account',
                f'{fb_account_id}-{user_id}'
            )
            account_action = fb_account.get('conversion_event')
        else:
            account_action = event.upper()
        if account_action is None:
            account_action = 'LINK_CLICK'

        now = datetime.datetime.now()
        dates = [
            {
                'since': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
                'until': (
                    now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            }
            for i in range(14, 0, -1)
        ]

        insights = acc.get_insights(
            params={'time_ranges': dates},
            fields=['spend', 'date_start', 'impressions', 'actions']
        )

        def get_conversions(actions):
            c = [
                a for a in actions if (
                    account_action in a['action_type'].upper()
                )
            ]
            if len(c) > 0:
                return float(c[0]['value'])
            else:
                return 0

        def get_clicks(actions):
            c = [
                a for a in actions if "LINK_CLICK" in a['action_type'].upper()
            ]
            if len(c) > 0:
                return float(c[0]['value'])
            else:
                return 0

        data = [
            {
                'impressions': float(i['impressions']),
                'spend': float(i['spend']),
                'conversions': get_conversions(i['actions']),
                'clicks': get_clicks(i['actions']),
                'date': i['date_start']
            }
            for i in insights
        ]
        return response.handler_response(
            200,
            data,
            'Success'
        )
    except Exception as e:
        logger.exception(f'Raised an Exception: {e}')
        return response.handler_response(
            200,
            [],
            f'Raised an Exception: {e}'
        )


def get_available_billing_plans_handler(event, context):
    '''
    Lambda handler to get available_billing_plans
    '''
    lambda_name = 'get_available_billing_plans'
    logger.info(
        'Received event in get_available_billing_plans: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    plan_data = get_available_billing_plans()
    return response.handler_response(
        200,
        plan_data,
        'Success'
    )


def subscribe_to_plan_handler(event, context):
    '''
    Lambda handler for subscribe_to_plan
    '''
    lambda_name = 'subscribe_to_plan'
    logger.info(
        'Received event in subscribe_to_plan: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    email = user_info.get('email')

    body_required_field = (
        'token', 'plan'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    token = resp.get('token')
    plan = resp.get('plan')

    customer = get_customer(email)
    if customer:
        logger.info("customer already exists")
        if not customer['sources']['data']:
            logger.info("adding card to customer")
            customer['source'] = token
            customer.save()

    granted_bonus = user_info.get('granted_bonus')
    new_credits = user_info.get('spend_credits_left', 0)
    if not granted_bonus:
        new_credits += 100
        granted_bonus = True
    client.update_item('User', user_id, {
        'customer_id': customer['id'],
        'granted_bonus': granted_bonus,
        'spend_credits_left': new_credits,
        'credit_plan': plan['name']
    })
    return response.handler_response(
        200,
        None,
        'Success'
    )
