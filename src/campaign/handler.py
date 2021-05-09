import json
import datetime
from decimal import Decimal

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.targetingsearch import TargetingSearch
from facebook_business.adobjects.adset import AdSet

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.batch import Batch
from utils.event import get_promoted_object
from .helpers import (
    get_campaign,
    accounts_get_selectable_events,
    get_account_pixels,
    get_account_mobile_apps,
    fb_get_active_audiences,
    fb_make_lookalikes,
    get_json_error_message,
    import_ad_helper,
    build_campaign_ownership_tree
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

    body_required_field = (
        'campaign_name', 'daily_budget', 'campaign_objective')
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    account = AdAccount(f'act_{fb_account_id}')

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
    fb_account_id = user_info.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id', 'page_id', 'app_url', 'interests', 'audience_list'
        'gender', 'min_age', 'max_age', 'country', 'conversion_event',
        'pixel_id', 'max_number_of_ads', 'adset_to_copy_targeting'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

    conversion_event = body.get('conversion_event')
    interests = body.get('interests')
    gender = body.get('gender')
    campaign_id = body.get('campaign_id')
    page_id = body.get('page_id')
    pixel_id = body.get('pixel_id')
    app_url = body.get('app_url')
    audience_list = body.get('audience_list')
    max_number_of_ads = body.get('max_number_of_ads')
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
            return (adset_id_list, exceptions)

    batch.execute()
    for adset in adset_list:
        if adset['id']:
            adset_id_list.append(adset['id'])

    logger.info(
        f'Created {len(adset_id_list)} adsets. ' +
        f'Example: {str(debug_example_adset)}')
    return (adset_id_list, exceptions)


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
    fb_account_id = user_info.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id',
        'campaign_name',
        'conversion_event',
        'campaign_type',
        'cpa_goal'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp

    body = json.loads(event['body'])

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

    campaign_info = client.get_item(pk, campaign_id)
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

    client.create_item(pk, campaign_id, campaign_data)

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


# def auto_expand(account_id, status,campaign_id,
#     conversion_event_name,daily_budget,cac,number_of_adsets,
#     name_template,access_token):
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
    fb_account_id = user_info.get('fb_account_id')
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
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

    conversion_event_name = body.get('conversion_event_name')[0]
    number_of_adsets = body.get('number_of_adsets')
    campaign_id = body.get('campaign_id')
    cac = body.get('cac')

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

    # with db.get_rds_db().cursor() as cur:
    #     expansion_query = """
    #     INSERT INTO expansion_config
    #     (campaign_id, expansion_enabled, autobid_budget, example_adset_id,
    #     adset_name_template, number_of_ad_sets)
    #     VALUES (%s, %s, %s, %s, %s, %s)
    #     ON CONFLICT (campaign_id) DO UPDATE
    #     SET expansion_enabled=%s, autobid_budget=%s, example_adset_id=%s,
    #         adset_name_template=%s, number_of_ad_sets=%s
    #     """
    #     cur.execute(expansion_query, (
    #     campaign_id, status, cac, example_adset_id, name_template, number_of_adsets,
    #     status, cac, example_adset_id, name_template, number_of_adsets
    #     ))

    #     campaign_query = """
    #     INSERT INTO campaigns
    #     (id, name, date_created, conversion_event, budget, status)
    #     VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
    #     ON CONFLICT (id) DO UPDATE
    #     SET conversion_event=%s, budget=%s
    #     """
    #     cur.execute(campaign_query, (
    #     campaign_id, campaign_name, date_created, conversion_event_name, daily_budget,
    #     conversion_event_name, daily_budget
    #     ))

    # segment_params = {
    #     'campaign_id':campaign_id,
    #     'user':user.get_email(),
    #     'status':status
    # }
    # segment.notify(account_id, "EXPANSION_STATUS", segment_params)
    # print("Updated database")


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
