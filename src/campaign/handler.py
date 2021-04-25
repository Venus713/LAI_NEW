import json
from decimal import Decimal
from dateutil.parser import parse

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.batch import Batch
from utils.constants import default_conversions

pk = 'User'

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()


def campaigns_conv_event_tuple_fix(conv_tuple_string):
    conv_tuple_string = conv_tuple_string.replace('{', '')
    conv_tuple_string = conv_tuple_string.replace('}', '')
    split_str = conv_tuple_string.split(',')

    return split_str[0]


def accounts_get_selectable_events(api, account_id):
    acct = AdAccount("act_%s" % account_id)
    # Standard set
    events = [(
        a.replace("_", " ").title(),
        (a, "default")
    ) for a in default_conversions]

    # Get all custom conversions
    try:
        cvs = list(
            acct.get_custom_conversions(fields=['name'], params={'limit': 500})
        )
        for c in cvs:
            events.append((
                c['name'].replace("_", " ").title() + " (custom conversion)",
                (c['id'], "custom_conversion")
            ))
    except Exception as e:
        logger.error(f'error in accounts_get_selectable_events: {e}')

    # Record the event ids that we already have so that we don't duplicate
    # with the custom events discovered through insights
    existing_event_ids = set([e[1] for e in events])

    # Get all actions from insights
    insights = acct.get_insights(
        params={'date_preset': 'last_90d'},
        fields=['actions']
    )
    if insights:
        for action in insights[0]['actions']:
            t = action['action_type']
        if t not in existing_event_ids:
            events.append((
                t.replace("_", " ").title() +
                " (custom event)", (t, "custom_event")))
    return sorted(events)


def campaigns_get_selectable_events_for_objective(account_id, objective):
    logger.info(
        'objective in campaigns_get_selectable_events_for_objective:' +
        f' {objective}')
    if objective.upper() == 'LINK_CLICKS':
        return [('Link Click', ('LINK_CLICK', 'default'))]
    elif objective.upper() == 'LEAD_GENERATION':
        return [('Lead', ('LEAD', 'default'))]
    elif objective.upper() == 'CONVERSIONS':
        return accounts_get_selectable_events(account_id)
    elif objective.upper() == 'APP_INSTALLS':
        return accounts_get_selectable_events(account_id)
    return []


def campaigns_get_selectable_events(api, account_id, campaign_id):
    campaign = Campaign(campaign_id, api=api)
    campaign.remote_read(fields=['objective', 'effective_status'])
    return campaigns_get_selectable_events_for_objective(
        account_id,
        campaign['objective']
    )


def ads_get_account_ads(account_id):
    ads = {}
    account_id = {
        'account_id': account_id
    }
    campaign_info = client.query_item(pk, account_id)
    ad_info = client.query_item('Ad', account_id)
    for cp in campaign_info:
        campaign_id = cp['campaign_id']
        for ad in ad_info:
            ad_id = ad_info['ad_id']
            c_a_res = client.get_item(f'Campaign-{campaign_id}', f'Ad-{ad_id}')

            if ad_id in ads:
                ads[ad_id]['campaigns'].append({
                    'id': campaign_id, 'name': c_a_res['campaign_name']
                })
            else:
                if campaign_id:
                    campaigns_value = [
                        {'id': campaign_id, 'name': c_a_res['campaign_name']}
                    ]
                else:
                    campaigns_value = []
                ads[ad_id] = {
                    'id': ad_id,
                    'name': c_a_res['ad_name'],
                    'preview': c_a_res['ad_preview'],
                    'created_at': c_a_res['ad_created_at'],
                    'status': c_a_res['enabled'],
                    'campaigns': campaigns_value
                    }

    return sorted(
        list(ads.values()),
        key=lambda x: x['created_at'],
        reverse=True
    )


def campaigns_get_ads(account_id, campaign_id):
    def is_in_campaign(ad):
        for c in ad['campaigns']:
            if c['id'] == int(campaign_id):
                return True
        return False

    all_ads = ads_get_account_ads(account_id)
    return [{
        'id': ad['id'],
        'name': ad['name'],
        'in_campaign': is_in_campaign(ad),
        'preview': ad['preview']
    } for ad in all_ads]


def get_campaign(
    api,
    account_id,
    campaign_id,
    preloaded_campaign_object=None,
    preloaded_db_row=None,
    skip_extras=False
):
    campaign_data = {}

    if preloaded_campaign_object is None:
        campaign = Campaign(campaign_id, api=api)
        campaign.remote_read(
            fields=['objective', 'effective_status', 'daily_budget', 'name'])
    else:
        campaign = preloaded_campaign_object

    adset = None

    if not skip_extras:
        try:
            adset = next(
                campaign.get_ad_sets(params={'limit': 1}, fields=['targeting'])
            )
        except Exception as e:
            logger.error(f'Error in get_campaign: {e}')
        if adset:
            targeting = adset['targeting']

            campaign_data['age_min'] = targeting.get('age_min', None)
            campaign_data['age_max'] = targeting.get('age_max', None)
            campaign_data['gender'] = targeting.get('genders', None)
            try:
                campaign_data['country'] = (
                    targeting['geo_locations']['cities'][0]['country'] +
                    " (More Specific)"
                )
            except Exception as e:
                logger.error(f'Error in get_campaign: {e}')
                try:
                    campaign_data['country'] = (
                        targeting['geo_locations']['countries'][0]
                    )
                except Exception as e:
                    logger.error(f'Error in get_campaign: {e}')
                    campaign_data['country'] = None
        campaign_data['exclusions'] = targeting.get(
            'excluded_custom_audiences',
            []
        )

    data = preloaded_db_row
    if preloaded_db_row is None:
        logger.info('preloaded_db_row is none')
        # with db.get_rds_db().cursor() as cur:
        #     query = '''
        #     SELECT c.id, c.name, c.campaign_type, c.conversion_event, c.budget, c.cpa_goal, c.date_created, c.status,
        #         exp.expansion_enabled, opt.optimization_enabled, exp.number_of_ad_sets, exp.adset_name_template, opt.number_of_ads
        #     FROM (
        #         campaigns c LEFT JOIN expansion_config exp
        #         ON c.id=exp.campaign_id
        #     )
        #     LEFT JOIN optimization_config opt
        #     ON c.id=opt.campaign_id
        #     WHERE c.id=%s
        #     '''
        #     cur.execute(query, (campaign_id,))
        #     data = cur.fetchone()

    def truthy(val):
        if val is None:
            return False
        elif isinstance(val, str):
            return val.lower() == "true"
        else:
            return bool(val)

    campaign_data['campaign_id'] = data[0] or 0
    campaign_data['campaign_name'] = campaign['name']
    campaign_data['campaign_type'] = data[2]
    if 'daily_budget' in campaign:
        campaign_data['daily_budget'] = int(campaign['daily_budget'])
    else:
        campaign_data['daily_budget'] = int(data[4]) or 0
    campaign_data['cpa_goal'] = int(data[5])*100 or 0
    campaign_data['date_created'] = parse(data[6]) if data[6] else None
    # campaign_data['campaign_status'] = data[7]
    campaign_data['auto_expansion_status'] = data[8] or False
    campaign_data['ad_optimization_status'] = data[9] or False
    campaign_data['auto_expansion_level'] = data[10] or 0
    campaign_data['naming_convention'] = data[11]
    campaign_data['ad_optimization_level'] = data[12] or 0

    logger.info(f'campaign data in get_campaign: {campaign_data}')

    # check to see if the conversion_event from db is a tuple, if it is,
    # update the record to the correct format.+
    if '{' in data[3] and '}' in data[3]:
        logger.info(
            f"campaign id {campaign_id} {campaign_data['campaign_name']}" +
            f" conversion_event is incorrectly formatted as {data[3]}")
        campaign_data['optimization_event'] = campaigns_conv_event_tuple_fix(
            data[3])
        logger.info(
            "will reformat db record to:" +
            f" {campaign_data['optimization_event']}"
        )
        # campaigns_update_row_value_db(
        #     'conversion_event', campaign_data['optimization_event'], 'campaigns', campaign_id, account_id)
    else:
        campaign_data['optimization_event'] = data[3]

    if skip_extras:
        campaign_data['account_optimization_events'] = []
    else:
        campaign_data['account_optimization_events'] = (
            campaigns_get_selectable_events(api, account_id, campaign_id)
        )

    if campaign['effective_status'] == 'ACTIVE':
        campaign_data['campaign_status'] = True
    else:
        campaign_data['campaign_status'] = False

    if skip_extras:
        campaign_data['ads_enabled'] = []
    else:
        campaign_data['ads_enabled'] = campaigns_get_ads(
            account_id, campaign_id)

    campaign_data['campaign_objective'] = campaign['objective']

    return campaign_data


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
        # try:
        #     campaign_data.append(campaigns_get_campaign(
        #         account_id,
        #         campaign['id'],
        #         preloaded_campaign_object=campaign,
        #         preloaded_db_row=row_by_id[int(campaign['id'])],
        #         skip_extras=True))
        # except Exception as e:
        #     print(e)

    return campaign_data
