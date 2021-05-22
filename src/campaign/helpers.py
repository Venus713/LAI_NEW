import json
import uuid
import os
import traceback
from dateutil.parser import parse
from decimal import Decimal
import collections

from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adspixel import AdsPixel
from facebook_business.adobjects.customaudience import CustomAudience
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.customconversion import CustomConversion
# from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.ad import Ad
from collections import defaultdict
import analytics
import boto3

from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.constants import default_conversions
from utils.exceptions import get_readable_fb_exception_details
from utils.batch import Batch

pk = 'Campaign'

sqs_client = boto3.client('sqs', region_name='us-east-1')
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


def accounts_get_selectable_events(fb_access_token, account_id):
    fb_api.get_facebook_api(fb_access_token)
    acct = AdAccount(f"act_{account_id}")
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
            int(campaign_info.get('daily_budget', 0))
        )
    campaign_data['cpa_goal'] = int(campaign_info.get('cpa_goal', 0))*100
    campaign_data['date_created'] = parse(campaign_info.get('created_at'))
    # campaign_data['campaign_status'] = data[7]
    campaign_data['auto_expansion_status'] = (
        campaign_info.get('expansion_enabled', False)
    )
    campaign_data['ad_optimization_status'] = (
        campaign_info.get('optimization_enabled', False)
    )
    campaign_data['auto_expansion_level'] = (
        campaign_info.get('number_of_ad_sets', 0)
    )
    campaign_data['naming_convention'] = (
        campaign_info.get('adset_name_template')
    )
    campaign_data['ad_optimization_level'] = (
        campaign_info.get('number_of_ads', 0)
    )

    logger.info(f'campaign data in get_campaign: {campaign_data}')

    # check to see if the conversion_event from db is a tuple, if it is,
    # update the record to the correct format.+
    if (
        '{' in campaign_info.get('conversion_event') and '}' in (
            campaign_info.get('conversion_event')
        )
    ):
        logger.info(
            f"campaign id {campaign_id} {campaign_data['campaign_name']}" +
            " conversion_event is incorrectly formatted "
            f"as {campaign_info.get('conversion_event')}")
        campaign_data['optimization_event'] = campaigns_conv_event_tuple_fix(
            campaign_info.get('conversion_event'))
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
            campaign_info.get('conversion_event')
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


def get_account_pixels(fb_access_token, account_id):
    pixel_id_list = []
    pixel_tuple = [('', 0)]

    fb_api.get_facebook_api(fb_access_token)

    account = AdAccount(f'act_{account_id}')
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


def get_account_mobile_apps(fb_access_token, account_id):
    fb_api.get_facebook_api(fb_access_token)
    account = AdAccount(f'act_{account_id}')
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


def fb_get_active_audiences(fb_access_token, account_id, ids=True):
    fb_api.get_facebook_api(fb_access_token)
    account = AdAccount(f'act_{account_id}')
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


def fb_make_lookalikes(fb_access_token, account_id, audience_id, country):
    try:
        fb_api.get_facebook_api(fb_access_token)
        account = AdAccount(f'act_{account_id}')
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
    sk = str(campaign_id) + '-' + str(canonical_id)
    client.create_item('Campaign-Ad', sk, campaign_ad_data)

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
            sk = str(campaign_id) + '-' + str(canonical_id)
            client.create_item(
                'Campaign-Ad', sk, campaign_ad_data)

    return canonical_id


def notify(account_id, name, params):
    analytics.write_key = '1cX2efK4R6oFInvsx57nMCIP5UDmG9zJ'

    analytics.track(
        int(account_id),
        name,
        params
    )


def make_request(req, fields=[], params={}):
    result = []
    response = req(fields=fields, params=params, pending=True).execute()
    for item in response:
        if isinstance(response.params, list):
            response.params = {}
        result.append(item.export_all_data())
    return result


def start_async_task(task, params):
    task_id = str(uuid.uuid4())
    client.create_item('AsyncResult', task_id, {'task': task})

    logger.info("Launching %s Task" % task, params)

    entries = {
        "task": task,
        "task_id": task_id,
        "params": params
    }
    print(f"{os.getenv('SQS_URL')=}")
    sqs_client.send_message(
        QueueUrl=os.getenv('SQS_URL'),
        MessageBody=json.dumps(entries),
        MessageGroupId='start_async_task'
    )

    return {"task_id": task_id}


def get_original_campaign(campaign):
    campaign.api_get(fields=['name', 'objective', 'daily_budget'])
    return campaign


def get_original_adsets(campaign):
    adsets = list(
        campaign.get_ad_sets(
            fields=['targeting', 'user_os', 'promoted_object']
        )
    )
    return adsets


def get_promoted_object(
    api, custom_event, user_os, application_id, object_store_url
):
    custom_event_name, custom_event_type = custom_event
    if custom_event_type == "custom_event":
        return {
            'pixel_id': application_id,
            'custom_event_type': 'OTHER',
            'pixel_rule': {
                'event': {'eq': custom_event_name},
            }
        }

    elif custom_event_type == "custom_conversion":
        cc = CustomConversion(custom_event_name, api)
        cc.remote_read(fields=['rule'])
        return {
            'pixel_id': application_id,
            'custom_event_type': 'OTHER',
            'pixel_rule': cc['rule']
        }

    # Default type
    else:
        # ####### NEED TO UPDATE THIS FOR MOBILE APPS
        if user_os:
            promoted_object = {
                'application_id': application_id,
                'object_store_url': object_store_url,
                'custom_event_type': custom_event_name,
            }

            return promoted_object

        else:
            return {
                'custom_event_type': custom_event_name,
                'pixel_id': application_id,
            }


def update_db_state(
    campaign_id,
    campaign_state,
    expansion_state,
    optimization_state,
    build_expansion=False,
    build_optimization=False,
    can_delete=False
):
    # build_expansion and build_optimization
    # allow this function to create new rows
    # can_delete is set during revert, which allows this function
    # to delete expansion or optimization config rows.
    if campaign_state:
        client.update_item(pk, campaign_id, campaign_state)

    if not expansion_state:
        if can_delete:
            client.update_item(pk, campaign_id, {
                'exp_number_of_ad_sets': None,
                'expansion_enabled': None,
                'exp_adset_name_template': None
            })
    else:
        client.update_item(pk, campaign_id, expansion_state)

    if not optimization_state:
        if can_delete:
            client.update_item(pk, campaign_id, {
                'opt_number_of_ads': None,
                'optimization_enabled': None
            })
    else:
        client.update_item(pk, campaign_id, optimization_state)


def dict_merge(dct, merge_dct):
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def update_campaign_adsets(api, campaign_id, changes, adsets=None):
    campaign = Campaign(campaign_id, api=api)
    if not adsets:
        adsets = campaign.get_ad_sets(
            fields=['id', 'targeting', 'promoted_object'])
    num_changes = 0
    results = []
    with Batch(api, results, raise_exceptions=True) as batcher:
        for adset in adsets:
            updates = adset.export_all_data()

            # And make the adset changes
            dict_merge(updates, changes)

            # Special case - promoted objects replace, not merge
            if 'promoted_object' in changes and changes['promoted_object']:
                updates['promoted_object'] = changes['promoted_object']

            # Special case - exclusions should replace, not merge
            if (
                'targeting' in changes and
                'excluded_custom_audiences' in changes['targeting']
            ):
                if 'targeting' not in updates:
                    updates['targeting'] = {}
                updates['targeting']['excluded_custom_audiences'] = (
                    changes['targeting']['excluded_custom_audiences']
                )

            print(updates)

            del updates['id']

            # Batch update
            adset.api_update(params=updates, batch=batcher.get_batch())

            num_changes += 1

    return (num_changes, [])


def update_adsets(
    api, campaign_id, adsets, fb_adset_values, fb_targeting_values
):
    if fb_targeting_values['targeting']:
        fb_adset_values['targeting'] = fb_targeting_values['targeting']
    return update_campaign_adsets(
        api, campaign_id, fb_adset_values, adsets=adsets
    )


def revert_db_state(campaign_id, original):
    campaign_state = original['campaign']
    expansion_state = original['expansion']
    optimization_state = original['optimization']

    update_db_state(
        campaign_id, campaign_state, expansion_state,
        optimization_state, can_delete=True
    )


def revert_campaign(original):
    params = original.export_all_data()
    del params['id']
    original.api_update(params=params)


def revert_adsets(originals):
    if not originals:
        return

    api = originals[0].get_api()
    with Batch(api) as batcher:
        for adset in originals:
            params = adset.export_all_data()
            del params['id']
            adset.api_update(params=params, batch=batcher.get_batch())


def update_campaign(user_id, fb_account_id, campaign_id, fields):
    logger.info(
        f"*** update_campaign *** \nuser_id:{user_id}"
        f"\nfb_account_id: \n{fb_account_id}")
    logger.info(
        f"*** update_campaign *** \ncampaign_id:{campaign_id}"
        f"\nfields: \n{fields}")
    sk = fb_account_id + '-' + user_id
    fb_access_token = client.get_item('FB_Account', sk)
    print(f'{fb_access_token=}')
    api = fb_api.get_facebook_api(fb_access_token)
    campaign = Campaign(campaign_id, api=api)

    logger.info("Storing original state")
    original_db_state = client.get_item(pk, campaign_id)
    original_campaign = get_original_campaign(campaign)
    original_adsets = get_original_adsets(campaign)

    logger.info("Assembling changes")
    fb_campaign_values = {}
    fb_targeting_values = {'targeting': {}}
    fb_adset_values = {}
    db_campaign_values = {}
    db_auto_expand_values = {}
    db_ad_optimization_values = {}
    changed_event = None

    if 'campaign_name' in fields:
        db_campaign_values['name'] = fields['campaign_name']
        fb_campaign_values['name'] = fields['campaign_name']

    if 'campaign_type' in fields:
        db_campaign_values['campaign_type'] = fields['campaign_type']

    if 'campaign_objective' in fields:
        fb_campaign_values['objective'] = fields['campaign_objective']

    if 'age_min' in fields:
        fb_targeting_values['targeting']['age_min'] = fields['age_min']

    if 'age_max' in fields:
        fb_targeting_values['targeting']['age_max'] = fields['age_max']

    if 'gender' in fields:
        fb_targeting_values['targeting']['genders'] = fields['gender']

    if 'country' in fields:
        fb_targeting_values['targeting']['geo_locations'] = {
            'countries': [fields['country']],
            'cities': None
        }

    if 'auto_expansion_level' in fields:
        db_auto_expand_values['exp_number_of_ad_sets'] = (
            fields['auto_expansion_level']
        )

    if 'auto_expansion_status' in fields:
        db_campaign_values['auto_expand'] = fields['auto_expansion_status']
        db_auto_expand_values['expansion_enabled'] = (
            fields['auto_expansion_status']
        )

    if 'naming_convention' in fields:
        db_auto_expand_values['exp_adset_name_template'] = (
            fields['naming_convention']
        )

    if 'ad_optimization_level' in fields:
        db_ad_optimization_values['opt_number_of_ads'] = (
            fields['ad_optimization_level']
        )

    if 'optimization_event' in fields:
        db_campaign_values['conversion_event'] = (
            fields['optimization_event'][0]
        )
        changed_event = fields['optimization_event']
        if original_adsets:
            reference_promo = original_adsets[0]['promoted_object']
            app_id = None
            obj_url = None
            user_os = None
            if 'pixel_id' in reference_promo:
                app_id = reference_promo['pixel_id']
            if 'application_id' in reference_promo:
                app_id = reference_promo['application_id']
            if 'object_store_url' in reference_promo:
                obj_url = reference_promo['object_store_url']
            if 'user_os' in original_adsets[0].get('targeting', {}):
                user_os = original_adsets[0]['targeting']['user_os']
            promoted_object = get_promoted_object(
                api, changed_event, user_os, app_id, obj_url
            )
            fb_adset_values['promoted_object'] = promoted_object

    if 'ad_optimization_status' in fields:
        db_campaign_values['ad_optimizer'] = fields['ad_optimization_status']
        db_ad_optimization_values['optimization_enabled'] = (
            fields['ad_optimization_status']
        )

    if 'daily_budget' in fields:
        db_campaign_values['budget'] = Decimal(fields['daily_budget'])
        fb_campaign_values['daily_budget'] = fields['daily_budget']

    if 'cpa_goal' in fields and fields['cpa_goal'] is not None:
        db_campaign_values['cpa_goal'] = Decimal(fields['cpa_goal'])

    if fields.get(
        'exclusions_added', []
    ) or fields.get('exclusions_removed', []):
        fb_targeting_values['targeting']['excluded_custom_audiences'] = (
            fields.get('exclusions', [])
        )

    logger.info("Making changes")
    # Now try to make all the changes, and revert everything if necessary
    try:
        try:
            if (
                db_campaign_values or
                db_auto_expand_values or
                db_ad_optimization_values
            ):
                logger.info("Found db changes, attempting DB update")
                build_expansion = (
                    db_auto_expand_values and
                    original_db_state['expansion'] == {}
                )
                build_optimization = (
                    db_ad_optimization_values and
                    original_db_state['optimization'] == {}
                )
                update_db_state(
                    campaign_id,
                    db_campaign_values,
                    db_auto_expand_values,
                    db_ad_optimization_values,
                    build_expansion=build_expansion,
                    build_optimization=build_optimization,
                    can_delete=False
                )
        except Exception as e:
            logger.error(e)
            raise Exception("Failed to update database")

        try:
            if fb_campaign_values:
                logger.info(
                    "Found campaign obj changes, "
                    "attempting FB object API update")
                campaign.api_update(params=fb_campaign_values)
        except FacebookRequestError as e:
            logger.info(traceback.format_exc)
            raise Exception(
                "Failed to update Facebook campaign: "
                f"{get_readable_fb_exception_details(e)}")
        except Exception as e:
            logger.error(e)
            logger.info(traceback.format_exc)
            raise Exception("Failed to update Facebook campaign")

        if fb_adset_values or fb_targeting_values['targeting']:
            logger.info(
                "Found adset changes, "
                "attempting FB object API update on each adset")
            num_success = 0
            errs = []
            try:
                update_adsets(
                    api, campaign_id, original_adsets,
                    fb_adset_values, fb_targeting_values
                )
            except FacebookRequestError as e:
                logger.info(traceback.format_exc)
                raise Exception(
                    "Failed to update Facebook adsets: "
                    f"{get_readable_fb_exception_details(e)}")
            except Exception as e:
                logger.error(e)
                logger.info(traceback.format_exc)
                raise Exception("Failed to update Facebook adsets")

            if errs and num_success == 0:
                raise Exception("Failed to update Facebook adsets")            

    except Exception as e:
        logger.error(f"Something went wrong: {e}")
        logger.info(traceback.format_exc())
        if (
            db_campaign_values or
            db_auto_expand_values or
            db_ad_optimization_values
        ):
            logger.info("Found db changes, reverting db changes")
            try:
                revert_db_state(campaign_id, original_db_state)
            except Exception as e:
                logger.error(f"Problem reverting: {e}")
                logger.info(traceback.format_exc())
        if fb_campaign_values:
            logger.info(
                "Found campaign obj changes, reverting campaign FB object")
            try:
                revert_campaign(original_campaign)
            except Exception as e:
                logger.error(f"Problem reverting: {e}")
                logger.info(traceback.format_exc())
        if fb_adset_values or fb_targeting_values['targeting']:
            logger.info("Found adset changes, reverting each adset FB object")
            try:
                revert_adsets(original_adsets)
            except Exception as e:
                logger.error(f"Problem reverting: {e}")
                logger.info(traceback.format_exc())
        raise

    logger.info("Done")
    return True
