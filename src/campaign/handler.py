import json
import datetime
import hashlib
import traceback
from decimal import Decimal
from operator import itemgetter

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.targetingsearch import TargetingSearch
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.page import Page

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.batch import Batch
from utils.event import get_promoted_object
from utils.stripe import Stripe
from .helpers import (
    get_campaign,
    accounts_get_selectable_events,
    get_account_pixels,
    get_account_mobile_apps,
    fb_get_active_audiences,
    fb_make_lookalikes,
    get_json_error_message,
    import_ad_helper,
    build_campaign_ownership_tree,
    notify,
    make_request,
    start_async_task,
    update_campaign
)

pk = 'Campaign'

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()
stripe: Stripe = Stripe()


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
    fb_account_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    data = accounts_get_selectable_events(fb_account_token, fb_account_id)

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
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    data = get_account_pixels(fb_access_token, fb_account_id)

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
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    data = get_account_mobile_apps(fb_access_token, fb_account_id)
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
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    data = fb_get_active_audiences(fb_access_token, fb_account_id)
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
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = ('audience_id', 'country', 'fb_account_id',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    data = fb_make_lookalikes(
        fb_access_token,
        resp['fb_account_id'],
        resp['audience_id'],
        resp['country'])
    return response.handler_response(
        200, data, 'Success in fb_make_lookalikes')


def create_campaign(event, context):
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
    fb_access_token = user_info.get('fb_access_token')
    fb_api.get_facebook_api(fb_access_token)

    body_required_field = (
        'campaign_name', 'daily_budget',
        'campaign_objective', 'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])
    fb_account_id = resp['fb_account_id']
    account = AdAccount(f"act_{fb_account_id}")

    try:
        campaign = account.create_campaign(params={
            'name': body.get('campaign_name'),
            'objective': body.get('campaign_objective'),
            'daily_budget': body.get('daily_budget'),
            'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
            'status': 'ACTIVE',
            'special_ad_categories': []
        })
    except FacebookRequestError as e:
        return response.fb_exception_response(e)

    logger.info(f"Created campaign: {campaign.get('id')}")

    campaign_data = {
        'fb_account_id': fb_account_id,
        'campaign_id': campaign.get('id'),
        'daily_budget': body.get('daily_budget'),
        'conversion_event': body.get('campaign_objective'),
        'active': True
    }
    client.create_item(pk, campaign.get('id'), campaign_data)
    logger.info('Added campaign to database')

    return response.handler_response(
        200, campaign.get('id'), 'Successfully created a campaign')


def create_fb_targeting_simple_handler(event, context):
    '''
    Lambda handler to create a fb_targeting_simple
    '''
    lambda_name: str = 'create_fb_targeting_simple'
    logger.info(
        'Received event in create_fb_targeting_simple: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id', 'page_id', 'app_url', 'interests', 'audience_list',
        'gender', 'min_age', 'max_age', 'country', 'conversion_event',
        'pixel_id', 'max_number_of_ads', 'adset_to_copy_targeting',
        'fb_account_id'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    conversion_event = body.get('conversion_event', {})
    interests = body.get('interests')
    gender = body.get('gender')
    campaign_id = body.get('campaign_id')
    page_id = body.get('page_id')
    pixel_id = body.get('pixel_id')
    app_url = body.get('app_url')
    audience_list = body.get('audience_list', [])
    max_number_of_ads = body.get('max_number_of_ads', 10)
    adset_to_copy_targeting = body.get('adset_to_copy_targeting')
    min_age = body.get('min_age')
    max_age = body.get('max_age')
    gender = body.get('gender')
    country = body.get('country')

    api = fb_api.get_facebook_api(fb_access_token)

    conversion_event, conversion_event_type = conversion_event

    exceptions = []
    debug_example_adset = None

    interests = interests.split(',')

    adset_list = []
    promoted_object = None

    # set the billing event. default to impressions (no choice for now).
    billing_event = 'IMPRESSIONS'

    # grab the campaign optimization goal.
    campaign = Campaign(campaign_id)

    campaign.api_get(fields=[
        Campaign.Field.name,
        Campaign.Field.effective_status,
        Campaign.Field.objective,
    ])

    if 'objective' in campaign:
        if campaign['objective'] == 'LINK_CLICKS':
            optimization_goal = 'LINK_CLICKS'
        elif campaign['objective'] == 'LEAD_GENERATION':
            optimization_goal = 'LEAD_GENERATION'
            promoted_object = {
                'page_id': page_id,
            }
        elif campaign['objective'] == 'APP_INSTALLS':
            optimization_goal = 'APP_INSTALLS'

        if conversion_event == 'INSTALL':
            promoted_object = {
                'application_id': pixel_id,
                'object_store_url': app_url,
            }
        else:
            promoted_object = {
                'application_id': pixel_id,
                'custom_event_type': conversion_event,
                'object_store_url': app_url,
            }
        if 'INSTALL' not in conversion_event:
            optimization_goal = 'OFFSITE_CONVERSIONS'
        else:
            optimization_goal = 'OFFSITE_CONVERSIONS'
            promoted_object = get_promoted_object(
                api,
                (conversion_event, conversion_event_type),
                None,
                pixel_id,
                None
            )
    else:
        optimization_goal = 'OFFSITE_CONVERSIONS'
        promoted_object = get_promoted_object(
            api,
            (conversion_event, conversion_event_type),
            None,
            pixel_id,
            None
        )

    ad_targeting_category_list = []
    adset_id_list = []
    ad_targeting_name_list = []

    if len(interests) > 0:
        ad_targeting_category = 'interests'

    if len(audience_list) > 0:
        ad_targeting_category = 'custom_audiences'

    if ad_targeting_category == 'interests' and len((interests[0])) >= 1:
        try:
            interests = interests.split(',')
        except Exception as e:
            logger.error(f'error in create_fb_targeting_simple: {e}')
        if ad_targeting_category == 'interests':
            for interest in interests:
                interest_list = TargetingSearch.search(
                    params={
                        'q': str(interest),
                        'type': 'adinterest'
                    })

                for item in interest_list:
                    interest_name = str(item['name']).lower()
                    interest = str(interest).lower()
                    if str(interest) in interest_name:
                        category = {
                            'id': item['id'],
                            'name': item['name']
                        }

                        ad_targeting_category_list.append(category)
                        ad_targeting_name_list.append(item['name'])
            if not ad_targeting_category_list:
                return response.handler_response(
                    400, None, 'No valid interests found')

    elif ad_targeting_category == 'custom_audiences':
        ad_targeting_category_list = ['Lookalike']

    else:
        ad_targeting_category_list = ['Broad']

    number_of_ads = 0

    def success_callback(result):
        pass

    def failure_callback(result):
        print(result.json())
        exceptions.append(
            {
                'error': get_json_error_message(result.json()),
                'campaign': campaign_id
            })

    i = 0

    batch_list = []
    batch = api.new_batch()
    batch_list.append(batch)

    for interest in ad_targeting_category_list:
        i = i+1
        if int(number_of_ads) < int(max_number_of_ads):
            if number_of_ads % 50 == 0:
                batch.execute()
                batch = api.new_batch()

            name = 'LAI'
            adset = AdSet(parent_id='act_'+str(fb_account_id))
            adset.update({'optimization_goal': optimization_goal})
            adset.update({'billing_event': billing_event})
            adset.update({'campaign_id': campaign_id})

            if promoted_object is not None:
                adset.update({'promoted_object': promoted_object})

            # create targeting for the adset
            targeting = {}
            if adset_to_copy_targeting is not None:
                copy_adset = AdSet(adset_to_copy_targeting)
                copy_adset.api_get(fields=['targeting'])
                targeting.update(copy_adset['targeting'])
                targeting['interests'] = None
                targeting['flexible_spec'] = None
            else:
                targeting.update({'age_min': min_age})
                targeting.update({'age_max': max_age})
                targeting.update({'genders': gender})
                targeting.update({'geo_locations': {'countries': country}})

            if len(audience_list) > 0:
                targeting.update({'custom_audiences': audience_list})

            if 'id' in interest:
                if len(interest['id']) > 1:
                    targeting.update({'interests': interest['id']})
                    name = str(interest.get('name'))
            else:
                name = str(interest)

            if len(app_url) > 0:
                if 'itunes' in app_url.lower():
                    targeting.update({'user_os': 'iOS'})
                elif 'play.google.com' in app_url.lower():
                    targeting.update({'user_os': 'Android'})

            adset.update({'targeting': targeting})

            name = name[:40]
            adset.update({'name': name})

            debug_example_adset = adset

            adset.remote_create(
                batch=batch,
                success=success_callback,
                failure=failure_callback,
                params={
                    'status': AdSet.Status.active,
                }
            )
            number_of_ads = number_of_ads + 1
            adset_list.append(adset)
        else:
            batch.execute()
            for adset in adset_list:
                if adset['id']:
                    adset_id_list.append(adset['id'])
            logger.info(
                f'Created {len(adset_id_list)} adsets. ' +
                'Example: {str(debug_example_adset)}')
            return response.handler_response(
                200,
                (adset_id_list, exceptions),
                'Success'
            )

    batch.execute()
    for adset in adset_list:
        if adset['id']:
            adset_id_list.append(adset['id'])

    logger.info(
        f'Created {len(adset_id_list)} adsets. ' +
        f'Example: {str(debug_example_adset)}')
    return response.handler_response(
        200,
        (adset_id_list, exceptions),
        'Success'
    )


def import_campaign_handler(event, context):
    '''
    Lambda handler to create a import_campaign
    '''
    lambda_name: str = 'create_import_campaign'
    logger.info(
        'Received event in create_import_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id',
        'campaign_name',
        'conversion_event',
        'campaign_type',
        'cpa_goal',
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    conversion_event = body.get('conversion_event')
    campaign_id = body.get('campaign_id')
    campaign_type = body.get('campaign_type')
    cpa_goal = body.get('cpa_goal')

    if isinstance(conversion_event, (list, tuple)):
        conversion_event = conversion_event[0]
    campaign_id = int(campaign_id)

    conversion_event = conversion_event or "PURCHASE"
    campaign_type = campaign_type or "Interests"
    cpa_goal = Decimal(cpa_goal or "10.50")

    campaign_info = client.get_item(pk, str(campaign_id))
    if campaign_info:
        logger.info(f'Campaign {campaign_id} has already has been imported')

    api = fb_api.get_facebook_api(fb_access_token)
    campaign = Campaign(campaign_id, api=api)
    campaign.api_get(fields=[
        'name', 'status', 'created_time', 'daily_budget'
    ])

    campaign['status'] == 'ACTIVE'
    daily_budget = Decimal(0)
    if 'daily_budget' in campaign:
        daily_budget = Decimal(campaign['daily_budget'])

    campaign_data = {
        'campaign_id': campaign_id,
        'fb_account_id': fb_account_id,
        'campaign_name': campaign.get('name'),
        'created_at': str(datetime.datetime.now()),
        'status': campaign['status'],
        'conversion_event': str(conversion_event),
        'budget': daily_budget,
        'cpa_goal': cpa_goal,
        'campaign_type': campaign_type
    }

    client.create_item(pk, str(campaign_id), campaign_data)

    tree = build_campaign_ownership_tree(api, fb_account_id)
    logger.debug(str(tree))
    for ad in campaign.get_ads(
        fields=['name', 'status', 'created_time', 'campaign_id', 'creative']
    ):
        logger.info(f"Importing campaign's ad {ad['name']}")
        import_ad_helper(
            api=api,
            ad=ad,
            account_id=fb_account_id,
            access_token=fb_access_token,
            campaign_ownership_tree=tree
        )

    return response.build_response(201, None, 'Successfully imported')


def auto_expand_handler(event, context):
    '''
    Lambda handler to create a auto_expand
    '''
    lambda_name: str = 'create_auto_expand'
    logger.info(
        'Received event in create_auto_expand: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
        'status',
        'campaign_id',
        'conversion_event_name',
        'daily_budget',
        'cac',
        'number_of_adsets',
        'name_template'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    conversion_event_name = body.get('conversion_event_name')[0]
    number_of_adsets = body.get('number_of_adsets')
    campaign_id = body.get('campaign_id')
    cac = body.get('cac')
    status = body.get('status')
    daily_budget = body.get('daily_budget')

    api = fb_api.get_facebook_api(fb_access_token)

    campaign = Campaign(campaign_id, api=api)
    campaign.api_get(fields=['name', 'created_time'])
    campaign_name = str(campaign['name'])
    date_created = campaign['created_time']

    example_adset_id = None
    ad_sets = campaign.get_ad_sets()

    if int(cac) < 1:
        cac = 1

    if len(ad_sets) > 0:
        example_adset_id = ad_sets[0]['id']
    else:
        return response.handler_response(
            400,
            None,
            'You must have at least 1 ad set in the campaign to run expansion.'
        )

    campaign_data = client.get_item(pk, campaign_id)
    data = {
        'campaign_id': campaign_id,
        'campaign_name': campaign_name,
        'created_at': date_created,
        'conversion_event': conversion_event_name,
        'budget': daily_budget,
        'status': 'ACTIVE',
        'expansion_enabled': status,
        'autobid_budget': cac,
        'example_adset_id': example_adset_id,
        'adset_name_template': example_adset_id,
        'number_of_ad_sets': number_of_adsets
    }
    if campaign_data:
        campaign_data.update(data)
        client.update_item(pk, campaign_id, campaign_data)
    else:
        client.create_item(pk, campaign_id, data)

    segment_params = {
        'campaign_id': campaign_id,
        'user': user_info.get('email'),
        'status': status
    }
    notify(fb_account_id, "EXPANSION_STATUS", segment_params)
    logger.info('Updated database')
    return response.handler_response(
        200,
        segment_params,
        'Success'
    )


def get_lead_forms_handler(event, context):
    '''
    Lambda handler to create a get_lead_forms
    '''
    lambda_name: str = 'create_get_lead_forms'
    logger.info(
        'Received event in create_get_lead_forms: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    api = fb_api.get_facebook_api(user_info.get('fb_access_token'))

    body_required_field = (
        'page_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    page_id = body.get('page_id')

    # from a FB page ID, return a list of leadform names.
    try:
        # create list of leadgen form names
        leadgen_form_names = []
        leadgen_forms = []

        # get list from FB
        page = Page(page_id, api=api)
        page.remote_read(fields=['access_token'])
        if 'access_token' in page:
            page_access_token = page['access_token']

            page_api = fb_api.get_facebook_api(page_access_token)
            page = Page(page_id, api=page_api)
            page.remote_read(fields=['leadgen_forms'])

        if 'leadgen_forms' in page:
            data = page['leadgen_forms']
            if 'data' in data:
                leadgen_forms = data['data']

        # cleanup to only get name.
        for form in leadgen_forms:
            print(form)
            if 'name' in form:
                leadgen_form_names.append((form['name'], form['id']))
        return response.handler_response(
            200,
            leadgen_form_names,
            'Success'
        )

    except Exception as e:
        logger.error(f'error in get_lead_forms: {e}')
        return response.exception_response(e)


def campaigns_get_adsets_handler(event, context):
    '''
    Lambda handler to create a campaigns_get_adsets
    '''
    lambda_name: str = 'create_campaigns_get_adsets'
    logger.info(
        'Received event in create_campaigns_get_adsets: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_api.get_facebook_api(user_info.get('fb_access_token'))

    body_required_field = (
        'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    campaign_id = body.get('campaign_id')

    campaign = Campaign(campaign_id)
    adset_list = list(campaign.get_ad_sets(fields=['name']))

    return response.handler_response(
        200,
        [(a['name'], a['id']) for a in adset_list],
        'Success'
    )


def get_ad_names_handler(event, context):
    '''
    Lambda handler to create a get_ad_names
    '''
    lambda_name: str = 'create_get_ad_names'
    logger.info(
        'Received event in create_get_ad_names: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')

    try:
        fb_api.get_facebook_api(fb_access_token)
        account = AdAccount(f'act_{fb_account_id}')

        ad_list = list(make_request(
            account.get_ads, fields=['id', 'name'], params={'limit': 200}
        ))

        ad_names = []
        ad_name_list = []
        for ad in ad_list:
            if ad['name'] not in ad_name_list:
                ad_name_list.append(ad['name'])
                ad_names.append(
                    {'name': ad['name'], 'id': ad['id'], 'build': False})

        return response.handler_response(
            200,
            ad_names,
            'Success'
        )

    except Exception as e:
        if 'message' in str(e):
            # raise Exception(e['message'])
            return response.handler_response(
                400,
                None,
                e['message']
            )
        else:
            logger.error(f'error in get_ad_names_handler: {e}')
            # raise Exception(
            #     "Sorry, looks like something went wrong. "
            #     "Please message support for help.")
            return response.handler_response(
                400,
                None,
                'Sorry, looks like something went wrong.' +
                'Please message support for help.'
            )


def get_current_billing_plan_handler(event, context):
    '''
    Lambda handler to create a get_current_billing_plan
    '''
    lambda_name: str = 'create_get_current_billing_plan'
    logger.info(
        'Received event in create_get_current_billing_plan: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)

    email = user_info.get('email')

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

    return response.handler_response(
        200,
        data,
        'Success'
    )


def get_fb_campaign_status_handler(event, context):
    '''
    Lambda handler to get get_fb_campaign_status
    '''
    lambda_name: str = 'get_fb_campaign_status'
    logger.info(
        'Received event in get_fb_campaign_status: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id', 'preloaded_campaign_object',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    campaign_id = body.get('campaign_id')
    preloaded_campaign_object = body.get('preloaded_campaign_object')

    api = fb_api.get_facebook_api(fb_access_token)

    if not preloaded_campaign_object:
        campaign = Campaign(campaign_id, api=api)
        campaign.remote_read(fields=['objective', 'effective_status'])
    else:
        campaign = preloaded_campaign_object

    return response.handler_response(
        200,
        campaign['effective_status'],
        'Success'
    )


def update_campaign_status_db_handler(event, context):
    '''
    Lambda handler to get update_campaign_status_db
    '''
    lambda_name: str = 'update_campaign_status_db'
    logger.info(
        'Received event in update_campaign_status_db: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'campaign_id', 'fb_status', 'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    campaign_id = body.get('campaign_id')
    fb_status = body.get('fb_status')

    campaign = client.get_item(pk, campaign_id)

    if campaign:
        if campaign.get('status') != fb_status:
            client.update_item(pk, campaign_id, {'status': fb_status})
    else:
        client.create_item(pk, campaign_id, {
            'fb_account_id': fb_account_id,
            'status': fb_status
        })
    return response.handler_response(
        200,
        None,
        'Success'
    )


def edit_fields_handler(event, context):
    '''
    Lambda handler for campaigns_edit_fields
    '''
    lambda_name: str = 'campaigns_edit_fields'
    logger.info(
        'Received event in campaigns_edit_fields: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'campaign_id', 'changes', 'originals',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    campaign_id = body.get('campaign_id')
    changes = body.get('changes')
    # originals = body.get('originals')

    data = json.dumps(changes)
    fb_account_id = client.get_item(pk, campaign_id).get('fb_account_id')
    if not fb_account_id:
        return response.handler_response(
            400,
            None,
            'Bad campaign_id'
        )

    params = {
        'user_id': user_id,
        'fb_account_id': fb_account_id,
        'campaign_id': campaign_id,
        'fields': data
    }

    task_id = start_async_task('update-campaign', params)
    return response.handler_response(
        200,
        {'task_id': task_id},
        'Success'
    )


def campaigns_check_async_handler(event, context):
    '''
    Lambda handler for campaigns_check_async
    '''
    lambda_name: str = 'campaigns_check_async'
    logger.info(
        'Received event in campaigns_check_async: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'asyncs', 'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    asyncs = body.get('asyncs')
    fb_account_id = body.get('fb_account_id')

    return_value = []
    for a in asyncs:
        campaign_id = a.get('campaign_id')
        task_id = a.get('task_id')
        async_task = client.get_item('AsyncResult', task_id)
        status = async_task.get('status')
        result = async_task.get('result')

        if result:
            result = json.loads(result)

        if status == 'done':
            campaign_data = get_campaign(fb_account_id, campaign_id)
            campaign_data['task_id'] = task_id
            return_value.append(campaign_data)
        if status == 'error':
            return_value.append(
                {
                    'task_id': task_id,
                    'error': result['error'],
                    'campaign_id': campaign_id
                }
            )
    return response.handler_response(
        200,
        return_value,
        'Success'
    )


def get_ad_account_info_handler(event, context):
    '''
    Lambda handler for get_ad_account_info
    '''
    lambda_name: str = 'get_ad_account_info'
    logger.info(
        'Received event in get_ad_account_info: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id', 'fb_account_name',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    fb_account_name = body.get('fb_account_name')

    fb_info = client.query_item(
        'FB_Account',
        {
            'fb_account_id': fb_account_id,
            'name': fb_account_name,
            'account_type': 'facebook'
        }
    )
    if not fb_info:
        return response.handler_response(
            400,
            None,
            'Bad fb_account_id or fb_account_name'
        )

    account_info = {
        'fb_access_token': fb_info[0].get('fb_access_token'),
        'fb_page_id': fb_info[0].get('fb_page_id'),
        'fb_instagram_id': fb_info[0].get('fb_instagram_id'),
    }

    if fb_info[0].get('fb_pixel_id'):
        account_info['fb_pixel_id'] = fb_info[0].get('fb_pixel_id')
    else:
        account_info['fb_app_id'] = fb_info[0].get('fb_app_id')

    return response.handler_response(
        200,
        account_info,
        'Success'
    )


def run_auto_expansion_handler(event, context):
    '''
    Lambda handler for run_auto_expansion
    '''
    lambda_name: str = 'run_auto_expansion'
    logger.info(
        'Received event in run_auto_expansion: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    user_info = client.get_item('User', user_id)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id', 'campaign_id',
        'maximum_number_adsets', 'starting_interest_list'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    campaign_id = body.get('campaign_id')
    maximum_number_adsets = body.get('maximum_number_adsets', 5)
    starting_interest_list = body.get('starting_interest_list')

    data = json.dumps({
        'fb_account_id': str(fb_account_id),
        'campaign_id': str(campaign_id),
        'max_adsets': int(maximum_number_adsets),
        'interests': starting_interest_list if starting_interest_list else [],
        'fb_access_token': user_info.get('fb_acccess_token'),
        'force_expand': True
    })
    resp = start_async_task('auto-expand', data)

    task_id = resp.get('task_id')
    return response.handler_response(
        200,
        {'task_id': task_id},
        'Success'
    )


def check_auto_expansion_handler(event, context):
    '''
    Lambda handler for check_auto_expansion
    '''
    lambda_name: str = 'check_auto_expansion'
    logger.info(
        'Received event in check_auto_expansion: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)

    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'task_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    task_id = body.get('task_id')

    async_task = client.get_item('AsyncResult', task_id)
    status = async_task.get('status')
    result = async_task.get('result')

    data = {
        'status': status,
        'result': result
    }
    return response.handler_response(
        200,
        data,
        'Success'
    )


def update_interests_handler(event, context):
    '''
    Lambda handler for update_interests
    '''
    lambda_name: str = 'update_interests'
    logger.info(
        'Received event in update_interests: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')
    api = fb_api.get_facebook_api(fb_access_token)

    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    campaign_id = body.get('campaign_id')

    campaign = Campaign(campaign_id, api=api)
    # get ad sets from campaign
    adset_list = make_request(
        campaign.get_ad_sets,
        fields=['name', 'targeting']
    )
    for adset in adset_list:
        try:
            adset = AdSet(adset['id'])
            adset.remote_read(fields=['name', 'targeting'])
            targeting = adset['targeting']
            if 'interests' in targeting or 'flexible_spec' in targeting:
                logger.info('skip in update_interests')
            else:
                interest_list = TargetingSearch.search(params={
                    'q': str(adset['name']),
                    'type': 'adinterest'
                })
                if len(interest_list) > 0:
                    interest = interest_list[0]
                    if str(
                        (adset['name']).lower()
                    ) in (interest['name'].lower()):
                        interests = {
                            'id': interest['id'],
                            'name': interest['name']
                        }

                targeting['interests'] = interests
                adset['targeting'] = targeting
                adset.remote_update()
                adset.remote_read(fields=['name', 'targeting'])
                targeting['interests'] = interests
                adset['targeting'] = targeting
                adset.remote_update()
                adset.remote_read(fields=['name', 'targeting'])

        except Exception as e:
            logger.error(f'error in update_interests: {e}')
            return response.handler_response(
                400,
                None,
                'Errro in updating interests'
            )
    return response.handler_response(
        200,
        None,
        'Success'
    )


def hide_campaign_handler(event, context):
    '''
    Lambda handler for hide_campaign
    '''
    lambda_name: str = 'hide_campaign'
    logger.info(
        'Received event in hide_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)

    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    campaign_id = body.get('campaign_id')

    campaign_contains_ads = client.query_item(
        'Campaign_Ad',
        {'campaign_id': campaign_id}
    )
    for c in campaign_contains_ads:
        sk = c.get('campaign_id') + '-' + c.get('ad_id')
        client.delete_item('Campaign_Ad', sk)
        client.delete_item(pk, c.get('campaign_id'))
    return response.handler_response(
        200,
        None,
        'Success'
    )


def accounts_get_custom_audiences_handler(event, context):
    '''
    Lambda handler for accounts_get_custom_audiences
    '''
    lambda_name: str = 'accounts_get_custom_audiences'
    logger.info(
        'Received event in accounts_get_custom_audiences: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)

    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')
    fb_api.get_facebook_api(fb_access_token)

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')

    acct = AdAccount("act_%s" % fb_account_id)
    resp = [
        {'id': a['id'], 'name': a['name']}
        for a in acct.get_custom_audiences(
            fields=['id', 'name'],
            params={'limit': 200}
        )
    ]
    return response.handler_response(
        200,
        resp,
        'Success'
    )


def get_importable_from_api_handler(event, context):
    '''
    Lambda handler for campaigns_get_importable_from_api
    '''
    lambda_name: str = 'campaigns_get_importable_from_api'
    logger.info(
        'Received event in campaigns_get_importable_from_api: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')

    api = fb_api.get_facebook_api(fb_access_token)

    account = AdAccount('act_' + str(fb_account_id), api=api)

    campaigns = make_request(
        account.get_campaigns, fields=['id', 'name'], params={'limit': 200}
    )

    campaign_list = []

    for campaign in campaigns:
        campaign_list.append((campaign['name'], campaign['id']))

    campaign_list_sorted = sorted(campaign_list, key=lambda c: c[0])
    hashed_data = hashlib.sha256(
        repr(campaign_list_sorted).encode('utf-8')
    ).hexdigest()

    data = {
        'importable': campaign_list_sorted,
        'hashed_data': hashed_data
    }
    logger.info(f"hashed value of data from api: {data['hashed_data']}")
    return response.handler_response(
        200,
        campaign_list_sorted,
        'Success'
    )


def get_expansion_interests_campaign_handler(event, context):
    '''
    Lambda handler for get_expansion_interests_campaign
    '''
    lambda_name: str = 'get_expansion_interests_campaign'
    logger.info(
        'Received event in get_expansion_interests_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)

    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'fb_account_id', 'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    fb_account_id = body.get('fb_account_id')
    campaign_id = body.get('campaign_id')

    fb_exp_inter_data = client.query_item('FB_Exp_Interests', {
        'fb_account_id': fb_account_id,
        'campaign_id': campaign_id
    })
    fb_exp_inter_data.sort(key=itemgetter('status'), reverse=False)
    fb_exp_inter_data.sort(key=itemgetter('date_created'), reverse=True)
    fb_exp_inter_data = fb_exp_inter_data[0:20]

    on_states = [
      'ACTIVE',
      'PENDING_REVIEW',
      'PREAPPROVED'
    ]

    res_data = [{
      'adset_interest': row.get('adset_interest'),
      'date_created': row.get('date_created').strftime("%m/%d/%Y"),
      'status': 'on' if row.get('status') in on_states else 'off'
    } for row in fb_exp_inter_data]

    return response.handler_response(
        200,
        res_data,
        'Success'
    )


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
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])
    fb_account_id = body.get('fb_account_id')

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

    row_by_id = {row.get('campaign_id'): row for row in campaign_rows}

    campaign_data = []
    for result in results:
        campaign_id = result.get('id')
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

    available_conversion_events = accounts_get_selectable_events(
        fb_access_token, fb_account_id)

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
        sk = c.get('campaign_id') + '-' + c.get('ad_id')
        client.delete_item('Campaign_Ad', sk)

    return response.handler_response(
        200, None, 'Successfully deleted')


def execute_async_task(event, context):
    '''
    handler to excute a SQS
    '''
    for record in event.get('Records'):
        body = json.loads(record.get('body'))
        print(f'{body=}')
        # task_name = body['task']
        task_id = body['task_id']
        params = body['params']

        try:
            client.update_item('AsyncResult', task_id, {'status': 'running'})
            result = update_campaign(**params)
            client.update_item('AsyncResult', task_id, {
                'result': json.dumps(result),
                'status': 'done',
                'failed': False,
                'done': True
            })
            return response.handler_response(
                200,
                None,
                'SQS task succeed.'
            )

        except Exception as err:
            print(traceback.format_exc())
            client.update_item('AsyncResult', task_id, {
                'result': json.dumps({"error": str(err)}),
                'status': 'error',
                'failed': True,
                'done': False
            })
            return response.handler_response(
                400,
                None,
                'SQS task raised exception.'
            )
