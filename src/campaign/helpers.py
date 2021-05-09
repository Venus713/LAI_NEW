import uuid
from dateutil.parser import parse
from decimal import Decimal

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adspixel import AdsPixel
from facebook_business.adobjects.customaudience import CustomAudience
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.ad import Ad
from collections import defaultdict

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.constants import default_conversions

pk = 'Campaign'

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

    campaign_info = preloaded_db_row

    if preloaded_db_row is None:
        logger.info('preloaded_db_row is none')
        campaign_info = client.get_item(pk, campaign_id)

    def truthy(val):
        if val is None:
            return False
        elif isinstance(val, str):
            return val.lower() == "true"
        else:
            return bool(val)

    campaign_data['campaign_id'] = campaign_id
    campaign_data['campaign_name'] = campaign_info['campaign_name']
    campaign_data['campaign_type'] = campaign_info['campaign_type']
    if 'daily_budget' in campaign:
        campaign_data['daily_budget'] = int(campaign['daily_budget'])
    else:
        campaign_data['daily_budget'] = (
            int(campaign_info[0].get('daily_budget')) or 0
        )
    campaign_data['cpa_goal'] = int(campaign_info[0].get('cpa_goal'))*100 or 0
    campaign_data['date_created'] = parse(campaign_info[0].get('created_at'))
    # campaign_data['campaign_status'] = data[7]
    campaign_data['auto_expansion_status'] = (
        campaign_info[0].get('expansion_enabled') or False
    )
    campaign_data['ad_optimization_status'] = (
        campaign_info[0].get('optimization_enabled') or False
    )
    campaign_data['auto_expansion_level'] = (
        campaign_info[0].get('number_of_ad_sets') or 0
    )
    campaign_data['naming_convention'] = (
        campaign_info[0].get('adset_name_template')
    )
    campaign_data['ad_optimization_level'] = (
        campaign_info[0].get('number_of_ads') or 0
    )

    logger.info(f'campaign data in get_campaign: {campaign_data}')

    # check to see if the conversion_event from db is a tuple, if it is,
    # update the record to the correct format.+
    if (
        '{' in campaign_info[0].get('conversion_event') and '}' in (
            campaign_info[0].get('conversion_event')
        )
    ):
        logger.info(
            f"campaign id {campaign_id} {campaign_data['campaign_name']}" +
            " conversion_event is incorrectly formatted "
            f"as {campaign_info[0].get('conversion_event')}")
        campaign_data['optimization_event'] = campaigns_conv_event_tuple_fix(
            campaign_info[0].get('conversion_event'))
        logger.info(
            "will reformat db record to:" +
            f" {campaign_data['optimization_event']}"
        )
        campaign_update_item = {
            'conversion_event': campaign_data['optimization_event']
        }
        client.update_item(
            pk, campaign_id, campaign_update_item
        )
    else:
        campaign_data['optimization_event'] = (
            campaign_info[0].get('conversion_event')
        )

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


def get_account_pixels(account_id):
    pixel_id_list = []
    pixel_tuple = [('', 0)]

    account = AdAccount('act_'+str(account_id))
    account.remote_read(fields=['adspixels'])

    if 'adspixels' in account:
        adspixels = account['adspixels']
        if 'data' in adspixels:
            data = adspixels['data']

        if len(data) > 0:
            for pixel_data in data:
                if 'id' in pixel_data:
                    pixel_id = pixel_data['id']
                    pixel_id_list.append(pixel_id)

    for pixel_id in pixel_id_list:
        pixel = AdsPixel(pixel_id)
        pixel.remote_read(fields=['name', 'id'])
        pixel_tuple.append((pixel['name'], pixel['id']))

    if len(pixel_tuple) > 1:
        pixel_sorted = sorted(pixel_tuple, key=lambda pixel: pixel[0])
        return pixel_sorted

    return pixel_tuple


def get_account_mobile_apps(account_id):
    account = AdAccount('act_'+str(account_id))
    account.get_advertisable_applications()

    app_tuple_list = [('', 0)]

    for app in account.get_advertisable_applications():
        if 'name' not in app:
            logger.info("no name in app")
        else:
            app_tuple_list.append((app['name'], app['id']))

    if len(app_tuple_list) > 1:
        app_sorted = sorted(app_tuple_list, key=lambda app: app[0])
        return app_sorted

    return app_tuple_list


def fb_get_active_audiences(account_id, ids=True):
    account = AdAccount('act_'+str(account_id))
    custom_audience_resp = account.get_custom_audiences(
        fields=['id', 'name'], params={'limit': 200}
    )
    custom_audience_list = []
    for item in custom_audience_resp:
        if isinstance(custom_audience_resp.params, list):
            custom_audience_resp.params = {}
        custom_audience_list.append(item.export_all_data())
    logger.info(f'{custom_audience_list=}')

    custom_audience_names = []

    for audience in custom_audience_list:
        if 'id' in audience:
            custom_audience_names.append((audience['name'], audience['id']))
        else:
            custom_audience_names.append(audience['name'])
    return custom_audience_names


def fb_make_lookalikes(account_id, audience_id, country):
    try:
        account = AdAccount('act_'+str(account_id))
        audience_list = []

        for i in [1, 2, 5]:
            lookalike = account.create_custom_audience(
                params={
                    'name': f'{audience_id}-{i}',
                    'subtype': CustomAudience.Subtype.lookalike,
                    'origin_audience_id': audience_id,
                    'lookalike_spec': {
                        'origin_audience_id': audience_id,
                        'ratio': float(Decimal(i)/(100)),
                        'country': country,
                    },
                })
            logger.info(
                "Created lookalike audience with ratio" +
                " %.2f: %s" % (float(Decimal(i) / 100), lookalike['id'])
            )

            audience_list.append(lookalike['id'])

        return audience_list

    except FacebookRequestError as e:
        raise Exception(e.api_error_message())
    except Exception as e:
        logger.error(f'exception in fb_make_lookalikes: {e}')
        raise Exception(
            "Sorry, looks like something went wrong. "
            "Please message support for help."
        )


def get_json_error_message(e):
    msg = ''
    if 'error' in e and 'error_user_msg' in e['error']:
        msg = e['error']['error_user_msg']
    else:
        msg = e['error']['message']
    return msg


def build_campaign_ownership_tree(api, fb_account_id):
    tree = defaultdict(set)
    campaigns = client.query_item(pk, {'fb_account_id': fb_account_id})
    for cp in campaigns:
        cpa = Campaign(cp.get('campaign_id'), api=api)
        for ad in cpa.get_ads(
            fields=['creative'], params={'limit': 100}
        ):
            tree[cp.get('campaign_id')].add(int(ad['creative']['id']))
    return dict(tree)


def import_ad_helper(
    api,
    ad=None,
    ad_id=None,
    fb_account_id=None,
    fb_access_token=None,
    campaign_ownership_tree=None
):
    if ad is None:
        ad = Ad(ad_id, api=api)
        ad.api_get(
            fields=[
                'name', 'status', 'created_time', 'campaign_id', 'creative']
        )

    canonical_id = int(ad['creative']['id'])
    campaign_id = int(ad['campaign_id'])

    preview = next(
        ad.get_previews(params={'ad_format': 'DESKTOP_FEED_STANDARD'})
    )['body']

    is_enabled = ad['status'] == 'ACTIVE'

    # Add the ad
    ad_data = {
        'ad_id': canonical_id,
        'fb_account_id': fb_account_id,
        'ad_name': ad.get('name'),
        'enabled': is_enabled,
        'created_at': ad.get('created_time'),
        'preview': preview
    }
    client.create_item('Ads', canonical_id, ad_data)

    campaign_ad_data = {
        'campaign_id': campaign_id,
        'ad_id': canonical_id
    }
    client.create_item('Campaign-Ad', str(uuid.uuid4()), campaign_ad_data)

    if campaign_ownership_tree is None:
        campaign_ownership_tree = build_campaign_ownership_tree(
            api, fb_account_id)

    for (
        other_campaign_id,
        creative_ids
    ) in campaign_ownership_tree.items():
        if canonical_id in creative_ids:
            logger.info(
                f'Also adding this ad to campaign {other_campaign_id}')

            campaign_ad_data = {
                'campaign_id': other_campaign_id,
                'ad_id': canonical_id
            }
            client.create_item(
                'Campaign-Ad', str(uuid.uuid4()), campaign_ad_data)

    return canonical_id
