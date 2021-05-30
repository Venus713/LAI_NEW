import json
import time
import datetime
from collections import defaultdict

from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreativevideodata import AdCreativeVideoData
from facebook_business.specs import ObjectStorySpec
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.advideo import AdVideo

from .helpers import (
    fb_create_single_image_creative, add_ad_to_campaign,
    register_new_ad, fb_preview_single_image_ad_helper
)
from utils.logging import logger
from utils.event_parser import EventParser
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI
from utils.batch import Batch
from utils.helpers import make_request

pk = 'Ads'

event_parser: EventParser = EventParser()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()


def get_account_ads_handler(event, context):
    '''
    Lambda handler to get account_ads
    '''
    lambda_name = 'get_account_ads'
    logger.info(
        'Received event in get_account_ads: ' +
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

    ads = {}
    data = []
    ads_info = client.query_item(pk, {'fb_account_id': fb_account_id})
    for ad in ads_info:
        ad_id = ad.get('ad_id')
        cps_ads = client.query_item('Campaign_Ad', {'ad_id': ad_id})
        for c_a in cps_ads:
            c = client.get_item('Campaign', c_a.get('campaign_id'))
            data.append({
                'ad_id': ad_id,
                'ad_name': ad.get('ad_name'),
                'ad_created_at': ad.get('created_at'),
                'ad_preview': ad.get('preview'),
                'ad_enabled': ad.get('enabled'),
                'campaign_id': c_a.get('campaign_id'),
                'campaign_name': c.get('campaign_name')
            })

    for d in data:
        ad_id = d.get('ad_id')
        campaign_id = d.get('campaign_id')
        campaign_name = d.get('campaign_name')
        ad_name = d.get('ad_name')
        ad_preview = d.get('ad_preview')
        ad_created_at = d.get('ad_created_at')
        ad_enabled = d.get('ad_enabled')
        if ad_id in ads:
            ads[ad_id]['campaigns'].append({
                'id': campaign_id, 'name': campaign_name
            })
        else:
            if campaign_id:
                campaigns_value = [{'id': campaign_id, 'name': campaign_name}]
            else:
                campaigns_value = []
            ads[ad_id] = {
                'id': ad_id,
                'name': ad_name,
                'preview': ad_preview,
                'created_at': ad_created_at,
                'status': ad_enabled,
                'campaigns': campaigns_value
            }

    res = sorted(
        list(ads.values()), key=lambda x: x['created_at'], reverse=True)

    return response.handler_response(
        200, res, 'Success')


def get_html_code_for_ad_preview_handler(event, context):
    '''
    Lambda handler to get html_code_for_ad_preview
    '''
    lambda_name = 'get_html_code_for_ad_preview'
    logger.info(
        'Received event in get_html_code_for_ad_preview: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'creative_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    creative_id = resp.get('creative_id')

    try:
        fb_api.get_facebook_api(fb_access_token)
        creative = AdCreative(creative_id)

        params = {'ad_format': 'DESKTOP_FEED_STANDARD', 'summary': 'true'}
        html_code = str(creative.get_previews(params=params)[0]['body'])

        logger.info(f'{html_code=}')

        return response.handler_response(
            200,
            {'html_code': html_code},
            'Success'
        )
    except FacebookRequestError as e:
        logger.exception(f'FacebookRequestError: {e}')
        msg = ""
        if 'error' in e.body() and 'error_user_msg' in e.body()['error']:
            msg = e.body()['error']['error_user_msg']
        else:
            msg = e.body()['error']['message']
        err_data = {
            "error": msg,
            "creative_id": creative_id
        }
        return response.handler_response(
            400,
            err_data,
            'Error'
        )

    except Exception as e:
        if 'message' in e:
            return response.handler_response(
                400,
                None,
                f"Exception: {e['message']}"
            )
        else:
            logger.error(e)
            return response.handler_response(
                400,
                None,
                (
                    'Execption: Sorry, looks like something went wrong. '
                    'Please message support for help.'
                )
            )


def import_ad_handler(event, context):
    '''
    Lambda handler for import_ad
    '''
    lambda_name = 'import_ad'
    logger.info(
        'Received event in import_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'ad_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    ad_id = resp.get('ad_id')

    try:
        ad = None
        campaign_ownership_tree = None
        api = fb_api.get_facebook_api(fb_access_token)
        if ad is None:
            ad = Ad(ad_id, api=api)
            ad.api_get(
                fields=[
                    'name',
                    'status',
                    'created_time',
                    'campaign_id',
                    'creative'
                ]
            )

        canonical_id = ad['creative']['id']
        campaign_id = ad['campaign_id']

        preview = next(
            ad.get_previews(params={'ad_format': 'DESKTOP_FEED_STANDARD'})
        )['body']

        is_enabled = ad['status'] == 'ACTIVE'

        client.create_item(pk, canonical_id, {
            'ad_id': canonical_id,
            'fb_account_id': fb_account_id,
            'name': ad['name'],
            'enabled': is_enabled,
            'created_at': ad['created_time'],
            'preview': preview
        })

        client.create_item(
            'Campaign_Ad',
            str(campaign_id) + '-' + str(canonical_id),
            {
                'campaign_id': campaign_id,
                'ad_id': canonical_id
            }
        )

        if campaign_ownership_tree is None:
            tree = defaultdict(set)
            campaigns = client.query_item(
                'Campaign', {'fb_account_id': fb_account_id})
            for c in campaigns:
                campaign = Campaign(c.get('campaign_id'), api=api)
                for ad in (
                    campaign.get_ads(
                        fields=['creative'], params={'limit': 100}
                    )
                ):
                    tree[campaign_id].add(int(ad['creative']['id']))

            campaign_ownership_tree = dict(tree)

        for (
            other_campaign_id, creative_ids
        ) in campaign_ownership_tree.items():
            if canonical_id in creative_ids:
                logger.info(
                    f"Also adding this ad to campaign {other_campaign_id}")
                client.create_item(
                    'Campaign_Ad',
                    str(other_campaign_id) + '-' + str(canonical_id),
                    {
                        'campaign_id': other_campaign_id,
                        'ad_id': canonical_id
                    })

        return response.handler_response(
            200,
            {'ad_id': canonical_id},
            'Success'
        )
    except Exception as e:
        logger.error(e)
        return response.handler_response(
            400,
            None,
            'Raised Exception error'
        )


def update_ad_status_from_campaign_handler(event, context):
    '''
    Lambda handler for update_ad_status_from_campaign
    '''
    lambda_name = 'update_ad_status_from_campaign'
    logger.info(
        'Received event in update_ad_status_from_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id', 'ad_name', 'status',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    campaign_id = resp.get('campaign_id')
    ad_name = resp.get('ad_name')
    status = resp.get('status')

    fb_api.get_facebook_api(fb_access_token)
    campaign = Campaign(campaign_id)

    ad_list = campaign.get_ads(fields=['name', 'id'])

    for ad in ad_list:
        if ad['name'] == ad_name:
            try:
                ad.update({'status': status})
                ad.remote_update()
            except Exception as e:
                logger.error(
                    'Raised Exception ' +
                    f'in update_ad_status_from_campaign_handler: {e}')
                return response.handler_response(
                    400,
                    None,
                    f'Raised Exception: {e}'
                )
    return response.handler_response(
        200,
        None,
        'Successfully updated!'
    )


def update_ad_status_handler(event, context):
    '''
    Lambda handler for update_ad_status
    '''
    lambda_name = 'update_ad_status'
    logger.info(
        'Received event in update_ad_status: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = (
        'ad_id', 'status',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    ad_id = resp.get('ad_id')
    status = resp.get('status')

    client.update_item(pk, ad_id, {'enabled': status})
    return response.handler_response(
        200,
        {
            'ad_id': ad_id,
            'enabled': status
        },
        'Successfully udpated!'
    )


def ads_remove_ad_from_campaign_handler(event, context):
    '''
    Lambda handler for ads_remove_ad_from_campaign
    '''
    lambda_name = 'ads_remove_ad_from_campaign'
    logger.info(
        'Received event in ads_remove_ad_from_campaign: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id', 'ad_creative_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    campaign_id = resp.get('campaign_id')
    ad_creative_id = resp.get('ad_creative_id')

    # FB part
    api = fb_api.get_facebook_api(fb_access_token)
    campaign = Campaign(campaign_id, api=api)
    with Batch(api) as batcher:
        for ad in campaign.get_ads(fields=['creative']):
            if str(ad['creative']['id']) == str(ad_creative_id):
                ad.remote_delete(batch=batcher.get_batch())

    # DB part
    client.delete_item(
        'Campaign_Ad',
        str(campaign_id) + '-' + str(ad_creative_id))
    return response.handler_response(
        200,
        {
            'id': str(campaign_id) + '-' + str(ad_creative_id)
        },
        'Successfully deleted!'
    )


def get_ad_account_info_handler(event, context):
    '''
    Lambda handler to get ad_account_info
    '''
    lambda_name = 'get_ad_account_info'
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
    fb_account_id = resp.get('fb_account_id')
    fb_account_name = resp.get('fb_account_name')

    fb_account_info = client.query_item(
        'FB_Account',
        {
            'fb_account_id': fb_account_id,
            'name': fb_account_name
        }
    )

    return response.handler_response(
        200,
        fb_account_info[0],
        'Success'
    )


def get_page_list_handler(event, context):
    '''
    Lambda handler to get page_list
    '''
    lambda_name = 'get_page_list'
    logger.info(
        'Received event in get_page_list: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    api = fb_api.get_facebook_api(fb_access_token)
    pages = User(fbid='me', api=api).get_accounts(fields=['name', 'id'])

    page_list = [
        (page['name'], page['id']) for page in pages if 'name' in page
    ]

    if page_list:
        pages_sorted = sorted(page_list, key=lambda page: page[0])
    else:
        pages_sorted = [('', 0)]

    return response.handler_response(
        200,
        pages_sorted,
        'Success'
    )


def get_lead_forms_handler(event, context):
    '''
    Lambda handler to get lead_forms
    '''
    lambda_name = 'get_lead_forms'
    logger.info(
        'Received event in get_lead_forms: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'page_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    page_id = resp.get('page_id')

    try:
        fb_api.get_facebook_api(fb_access_token)

        leadgen_form_names = []
        leadgen_forms = []

        # get list from FB
        page = Page(page_id)
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
            logger.info(form)
            if 'name' in form:
                leadgen_form_names.append((form['name'], form['id']))
        return response.handler_response(
            200,
            leadgen_form_names,
            'Success'
        )

    except Exception as e:
        logger.error(f'Raised Exception in get_lead_forms_handler: {e}')
        return response.handler_response(
            400,
            None,
            (
                'Sorry, looks like something went wrong. '
                'Please message support for help.'
            )
        )


def get_account_ad_names_handler(event, context):
    '''
    Lambda handler to get account_ad_names
    '''
    lambda_name = 'get_account_ad_names'
    logger.info(
        'Received event in get_account_ad_names: ' +
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

    try:
        fb_api.get_facebook_api(fb_access_token)
        account = AdAccount('act_'+str(fb_account_id))
        ad_list = list(make_request(
            account.get_ads, fields=['id', 'name'], params={'limit': 200}
        ))

        ad_list_by_adset = defaultdict(list)
        i = 0
        for ad in ad_list:
            if i % 500 == 0:
                print(ad, i)
            ad_list_by_adset[ad['id']].append(ad['name'])
            i += 1

        return response.handler_response(
            200,
            list(ad_list_by_adset.items()),
            'Success'
        )

    except Exception as e:
        if 'message' in e:
            return response.handler_response(
                400,
                None,
                (
                    "Raised Exception in get_account_ad_names_handler :"
                    f" {e['message']}"
                )
            )
        else:
            return response.handler_response(
                400,
                None,
                (
                    "Sorry, looks like something went wrong. "
                    "Please message support for help."
                )
            )


def get_insta_page_id_handler(event, context):
    '''
    Lambda handler to get insta_page_id
    '''
    lambda_name = 'get_insta_page_id'
    logger.info(
        'Received event in get_insta_page_id: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'page_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    page_id = resp.get('page_id')

    try:
        fb_api.get_facebook_api(fb_access_token)
        page = Page(page_id)

        page.remote_read(fields=['access_token'])
        if 'access_token' in page:
            page_access_token = page['access_token']
            page_api = fb_api.get_facebook_api(page_access_token)
            page = Page(page_id, api=page_api)
            page.remote_read(fields=['page_backed_instagram_accounts'])

            if 'page_backed_instagram_accounts' in page:
                logger.info("page backed insta account")
                if 'data' in page['page_backed_instagram_accounts']:
                    data = page['page_backed_instagram_accounts']['data']
                    logger.info(data)
                    if len(data) > 0:
                        insta_data = data[0]
                        logger.info(insta_data)

                        if 'id' in insta_data:
                            insta_id = insta_data['id']
                            logger.info("got page insta ID "+str(insta_id))

                            return response.handler_response(
                                200,
                                {'insta_id': insta_id},
                                'Success'
                            )
                        return response.handler_response(
                            400,
                            None,
                            'Does not exist id in a insta_data.'
                        )
                    return response.handler_response(
                        400,
                        None,
                        'data in a page_backed_instagram_accounts is empty.'
                    )
                return response.handler_response(
                    400,
                    None,
                    'Doest not exist data in a page_backed_instagram_accounts.'
                )
            return response.handler_response(
                400,
                None,
                (
                    'Does not exist a page_backed_instagram_accounts'
                    f' in {page}.'
                )
            )
        return response.handler_response(
            400,
            None,
            'Does not exist the access_token in {page}'
        )

    except Exception as e:
        return response.handler_response(
            400,
            None,
            f'Raised Exception in get_insta_page_id: {e}'
        )


def fb_get_active_adsets_handler(event, context):
    '''
    Lambda handler for fb_get_active_adsets
    '''
    lambda_name = 'fb_get_active_adsets'
    logger.info(
        'Received event in fb_get_active_adsets: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    campaign_id = resp.get('campaign_id')

    try:
        fb_api.get_facebook_api(fb_access_token)
        campaign = Campaign(campaign_id)
        adset_list = campaign.get_ad_sets()

        adset_id_list = []

        for adset in adset_list:
            adset_id = adset['id']
            adset_id_list.append(adset_id)

        return response.handler_response(
            200,
            adset_id_list,
            'Success'
        )

    except Exception as e:
        if 'message' in e:
            return response.handler_response(
                400,
                None,
                (
                    "Raised Exception in fb_get_active_adsets_handler :"
                    f" {e['message']}"
                )
            )
        else:
            return response.handler_response(
                400,
                None,
                (
                    "Sorry, looks like something went wrong. "
                    "Please message support for help."
                )
            )


def fb_create_single_image_ad_handler(event, context):
    '''
    Lambda handler for fb_create_single_image_ad
    '''
    lambda_name = 'fb_create_single_image_ad'
    logger.info(
        'Received event in fb_create_single_image_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'page_id', 'instagram_actor_id', 'campaign_id',
        'adset_id_list', 'call_to_action_type', 'image', 'ad_copy',
        'ad_caption', 'url', 'ad_name', 'pixel_id', 'link_title',
        'ad_description', 'deep_link', 'leadgen_form_id', 'acct_ad_names',
        'creative_cache'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    instagram_actor_id = resp.get('instagram_actor_id')
    campaign_id = resp.get('campaign_id')
    adset_id_list = resp.get('adset_id_list')
    call_to_action_type = resp.get('call_to_action_type')
    image = resp.get('image')
    ad_copy = resp.get('ad_copy')
    ad_caption = resp.get('ad_caption')
    url = resp.get('url')
    ad_name = resp.get('ad_name')
    pixel_id = resp.get('pixel_id')
    link_title = resp.get('link_title')
    ad_description = resp.get('ad_description')
    deep_link = resp.get('deep_link')
    leadgen_form_id = resp.get('leadgen_form_id')
    acct_ad_names = resp.get('acct_ad_names')
    creative_cache = resp.get('creative_cache')

    if creative_cache is None:
        creative_cache = {}
    exceptions = []

    def success_callback(result):
        logger.info('success')

    def failure_callback(result):
        logger.info(result.json())
        exceptions.append(
            {
                'error': result.json()['error']['error_user_msg'],
                'campaign': campaign_id
            }
        )

    ad_list = []
    ad_id_list = []
    # adset_update_id_list = []
    # creative_count = 0
    # creative_list = []
    ad_count = 0
    api = fb_api.get_facebook_api(fb_access_token)
    AdAccount('act_'+str(fb_account_id))
    ad_batch = api.new_batch()

    cache_hash_elems = [
        fb_account_id,
        page_id,
        instagram_actor_id,
        call_to_action_type,
        image.name,
        ad_copy,
        ad_caption,
        url,
        ad_name,
        link_title,
        ad_description,
        deep_link
    ]
    cache_hash = str(hash(frozenset(cache_hash_elems)))
    if cache_hash in creative_cache:
        logger.info('found in cache')
        creative_id = creative_cache[cache_hash]
    else:
        logger.info('not found in cache, making new creative')

        creative_id, creative_exceptions = fb_create_single_image_creative(
            api,
            fb_account_id,
            page_id,
            instagram_actor_id,
            call_to_action_type,
            image,
            ad_copy,
            ad_caption,
            url,
            ad_name,
            link_title,
            ad_description,
            deep_link,
            leadgen_form_id
        )
        if len(creative_exceptions) > 0:
            return (
                [],
                creative_cache,
                [{
                    'error': exc, 'campaign': campaign_id
                } for exc in creative_exceptions]
            )
        creative_cache[cache_hash] = creative_id

    ad_creative = AdCreative(creative_id)
    ad_creative.remote_read(
        fields=[
            'effective_object_story_id',
            'effective_instagram_story_id',
            'instagram_actor_id'
        ]
    )
    logger.info(ad_creative)
    creative = AdCreative(parent_id='act_'+str(fb_account_id))
    creative.update(
        {
            'object_story_id': ad_creative['effective_object_story_id']
        }
    )

    if 'effective_instagram_story_id' in ad_creative:
        creative.update(
            {
                'effective_instagram_story_id': (
                    ad_creative['effective_instagram_story_id']
                )
            }
        )

    if 'instagram_actor_id' in ad_creative:
        logger.info('found insta actor id')
        creative.update(
            {
                'instagram_actor_id': ad_creative['instagram_actor_id']
            }
        )

    if str(fb_account_id) == '1396597360629452':
        creative.update({'authorization_category': 'POLITICAL'})

    logger.info(creative)
    creative.remote_create()

    creative_id = creative['id']

    # create call to action for the link data
    for adset_id in adset_id_list:
        adset = AdSet(adset_id)
        update = True

        if acct_ad_names is not None:
            if adset_id in acct_ad_names:
                if ad_name in acct_ad_names[adset_id]:
                    logger.info(
                        f'ad name {ad_name} exists in adset {adset_id}'
                    )
                    update = False
        else:
            try:
                logger.info(
                    "didn't have ad names, forced to use slow API call"
                )
                ads = adset.get_ads(fields={Ad.Field.name, Ad.Field.id})
                for ad in ads:
                    if ad['name'] == ad_name:
                        logger.info(
                            f'ad name {ad_name} exists in adset {adset_id}'
                        )
                        update = False
            except Exception as e:
                logger.exception(
                    f'Exception in fb_create_single_image_ad_handler: {e}'
                )
                update = True
        if update:
            logger.info(f'ad name {ad_name} NOT in adset {adset_id}')
            if ad_count % 50 == 0:
                logger.info('ad batch execute')
                ad_batch.execute()
                ad_batch = api.new_batch()
                logger.info('ready for another 50')
            ad = Ad(parent_id='act_'+str(fb_account_id))
            ad[Ad.Field.name] = ad_name
            ad[Ad.Field.adset_id] = adset_id
            if pixel_id > '0' and 'itunes' not in url and 'google' not in url:
                ad[Ad.Field.tracking_specs] = [{
                    'action.type': 'offsite_conversion',
                    'fb_pixel': pixel_id,
                }]
            ad[Ad.Field.creative] = {'creative_id': creative_id}
            ad.remote_create(
                batch=ad_batch,
                success=success_callback,
                failure=failure_callback
            )
            ad_list.append(ad)
            ad_count = ad_count + 1

    logger.info('ad batch execute')
    ad_batch.execute()
    logger.info('ad list')

    ad_id_list = []
    for ad in ad_list:
        ad_id_list.append(ad['id'])

    if not exceptions:
        client.create_item(pk, creative_id, {
            'ad_id': creative_id,
            'fb_account_id': fb_account_id,
            'name': ad_name,
            'enabled': True,
            'created_at': str(datetime.datetime.now())
        })
        client.create_item(
            'Campaign_Ad',
            str(campaign_id) + '-' + str(creative_id),
            {
                'campaign_id': campaign_id,
                'ad_id': creative_id
            }
        )

    return response.handler_response(
        200,
        (ad_id_list, creative_cache, exceptions),
        'Success'
    )


def fb_create_video_ad_handler(event, context):
    '''
    Lambda handler for fb_create_video_ad
    '''
    lambda_name = 'fb_create_video_ad'
    logger.info(
        'Received event in fb_create_video_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'page_id', 'instagram_actor_id', 'campaign_id',
        'adset_id_list', 'call_to_action_type', 'video_id', 'image', 'ad_copy',
        'ad_caption', 'url', 'ad_name', 'pixel_id', 'link_title',
        'ad_description', 'leadgen_form_name',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    instagram_actor_id = resp.get('instagram_actor_id')
    campaign_id = resp.get('campaign_id')
    adset_id_list = resp.get('adset_id_list')
    call_to_action_type = resp.get('call_to_action_type')
    image = resp.get('image')
    ad_copy = resp.get('ad_copy')
    ad_caption = resp.get('ad_caption')
    url = resp.get('url')
    ad_name = resp.get('ad_name')
    pixel_id = resp.get('pixel_id')
    # link_title = resp.get('link_title')
    ad_description = resp.get('ad_description')
    # leadgen_form_name = resp.get('leadgen_form_name')
    video_id = resp.get('video_id')

    all_exceptions = []

    def success_callback(result):
        logger.info("success")

    def failure_callback(result):

        try:
            all_exceptions.append(
                {
                    'error': result.json()['error']['error_user_msg'],
                    'campaign': campaign_id
                }
            )
            logger.info(result.json())
        except Exception as e:
            logger.exception(f'Exception in failure_callback: {e}')

    try:
        api = fb_api.get_facebook_api(fb_access_token)
        creative_batch = api.new_batch()
        ad_batch = api.new_batch()
        ad_list = []
        ad_id_list = []
        # adset_update_id_list = []
        creative_count = 0
        # creative_list = []
        ad_count = 0

        with open("/tmp/image.png", "wb") as fd:
            fd.write(image.get_bytes())
        file_image = "/tmp/image.png"

        image = AdImage(parent_id='act_'+str(fb_account_id))
        image[AdImage.Field.filename] = file_image
        image.remote_create()

        if creative_count % 50 == 0:
            logger.info('batch creative')
            creative_batch.execute()
            creative_batch = api.new_batch()

        leadgen_form_id = 0

        video_data = AdCreativeVideoData()
        video_data.update({
            'call_to_action': {
                'type': call_to_action_type,
                'value': {
                    'link': url,
                },
            },
        })
        # add leadgen form if selected
        if leadgen_form_id > 0:
            video_data['call_to_action']['value'].update(
                {
                    'lead_gen_form_id': leadgen_form_id
                }
            )

        video_data.update({'title': ad_caption})
        video_data.update({'video_id': video_id})
        video_data.update({'image_hash': image[AdImage.Field.hash]})
        video_data.update({'message': ad_copy})
        video_data.update({'link_description': ad_description})

        object_story_spec = ObjectStorySpec()
        object_story_spec.update({'video_data': video_data})
        object_story_spec.update({'page_id': page_id})
        if int(instagram_actor_id) > 0:
            object_story_spec.update(
                {'instagram_actor_id': instagram_actor_id}
            )

        creative2 = AdCreative(parent_id='act_'+str(fb_account_id))
        creative2[AdCreative.Field.name] = ad_name
        creative2['body'] = ad_copy
        creative2['title'] = ad_caption
        creative2[AdCreative.Field.object_story_spec] = object_story_spec
        if str(instagram_actor_id) > '0':
            creative2.update({'instagram_actor_id': instagram_actor_id})

        if str(fb_account_id) == '1396597360629452':
            creative2.update({'authorization_category': 'POLITICAL'})

        if fb_account_id == '1388855401347764':
            creative2['url_tags'] = (
                'utm_medium=ppc&utm_source=Facebook&utm_campaign='
                '{{campaign.id}}&utm_term={{adset.id}}&utm_content='
                '{{ad.id}}_{{placement}}'
            )
        elif fb_account_id == '10369968':
            creative2['url_tags'] = (
                'try=creativeteams&utm_source=facebook&utm_campaign='
                '{{campaign.id}}&utm_content={{ad.id}}'
            )
        else:
            creative2['url_tags'] = (
                'utm_source={{site_source_name}}&utm_campaign='
                '{{campaign.id}}&utm_adset={{adset.id}}&utm_ad={{ad.id}}'
            )

        logger.info('added story')
        logger.info(creative2.export_all_data())
        creative2.remote_create()
        logger.info(creative2)

        logger.info('make creative')

        for adset_id in adset_id_list:
            adset = AdSet(adset_id)
            update = True
            try:
                ads = adset.get_ads(fields={Ad.Field.name, Ad.Field.id})
                for ad in ads:
                    if ad['name'] == ad_name:
                        update = False
            except Exception as e:
                logger.exception(f'Exception: {e}')
                update = True
            if update:
                logger.info(f'ad name {ad_name} NOT in adset {adset_id}')
                if ad_count % 50 == 0:
                    logger.info('ad batch execute')
                    ad_batch.execute()
                    ad_batch = api.new_batch()
                    logger.info('ready for another 50')
                ad = Ad(parent_id='act_'+str(fb_account_id))
                ad[Ad.Field.name] = ad_name
                ad[Ad.Field.adset_id] = adset_id
                if (
                    pixel_id > '0' and
                    'itunes' not in url and
                    'google' not in url
                ):
                    ad[Ad.Field.tracking_specs] = [{
                        'action.type': 'offsite_conversion',
                        'fb_pixel': pixel_id,
                    }]
                    logger.info('tracking field specs')
                ad[Ad.Field.creative] = {'creative_id': creative2['id']}
                logger.info(ad)
                ad.remote_create(
                    batch=ad_batch,
                    success=success_callback,
                    failure=failure_callback
                )
                ad_list.append(ad)
                ad_count = ad_count + 1

        logger.info('ad batch execute')
        ad_batch.execute()
        logger.info('ad list')

        ad_id_list = []
        for ad in ad_list:
            ad_id_list.append(ad['id'])

        if not all_exceptions:
            client.create_item(pk, creative2['id'], {
                'ad_id': creative2['id'],
                'fb_account_id': fb_account_id,
                'name': ad_name,
                'enabled': True,
                'created_at': str(datetime.datetime.now())
            })
            client.create_item(
                'Campaign_Ad',
                str(campaign_id) + '-' + str(creative2['id']),
                {
                    'campaign_id': campaign_id,
                    'ad_id': creative2['id']
                }
            )

        logger.info(ad_id_list)
        return response.handler_response(
            200,
            (ad_id_list, all_exceptions),
            'Success'
        )

    except FacebookRequestError as e:
        logger.exception(f'FacebookRequestError: {e}')
        msg = ""
        if 'error' in e.body() and 'error_user_msg' in e.body()['error']:
            msg = e.body()['error']['error_user_msg']
        else:
            msg = e.body()['error']['message']
        data = ([], [{
            "error": msg,
            "campaign": campaign_id
        }])
        return response.handler_response(
            400,
            data,
            'Error'
        )


def copy_unimported_ad_handler(event, context):
    '''
    Lambda handler for ads_copy_unimported_ad
    '''
    lambda_name = 'ads_copy_unimported_ad'
    logger.info(
        'Received event in ads_copy_unimported_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'ad_id', 'campaign_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    ad_id = resp.get('ad_id')
    campaign_id = resp.get('campaign_id')

    api = fb_api.get_facebook_api(fb_access_token)
    ad = Ad(ad_id, api=api)
    ad.api_get(fields=['creative', 'name'])
    res, msg = add_ad_to_campaign(
        api, fb_account_id, campaign_id, ad['creative']['id'], ad['name']
    )
    if res:
        return response.handler_response(
            200,
            None,
            msg
        )
    else:
        return response.handler_response(
            400,
            None,
            msg
        )


def fb_create_post_ad_handler(event, context):
    '''
    Lambda handler for fb_create_post_ad
    '''
    lambda_name = 'fb_create_post_ad'
    logger.info(
        'Received event in fb_create_post_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'adset_id_list', 'campaign_id', 'page_id',
        'post_id_list', 'name', 'pixel_id', 'instagram_id'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    campaign_id = resp.get('campaign_id')
    adset_id_list = resp.get('adset_id_list')
    post_id_list = resp.get('post_id_list')
    name = resp.get('name')
    pixel_id = resp.get('pixel_id')
    instagram_id = resp.get('instagram_id')

    exceptions = []

    try:
        api = fb_api.get_facebook_api(fb_access_token)
        ad_batch = api.new_batch()

        ad_count = 0
        post_id_list = post_id_list.split(',')

        logger.info(post_id_list)

        for post_id in post_id_list:
            logger.info(post_id)
            creative = AdCreative(parent_id='act_'+str(fb_account_id))
            creative['name'] = post_id
            creative['object_story_id'] = f'{page_id}_{post_id}'
            if instagram_id > '0':
                creative['instagram_actor_id'] = instagram_id
            creative.remote_create()

            logger.info("creative ID: "+str(creative['id']))

            for adset_id in adset_id_list:
                try:
                    ads = AdSet.get_ads(fields={Ad.Field.name, Ad.Field.id})
                    for ad in ads:
                        if ad['name'] == name:
                            update = False
                except Exception as e:
                    logger.exception(f'Exception: {e}')
                    update = True
                if update:
                    ad = Ad(parent_id='act_'+str(fb_account_id))
                    if ad_count % 50 == 0:
                        ad_batch.execute()
                        ad_batch = api.new_batch()

                    ad['name'] = str(name)
                    ad['adset_id'] = adset_id
                    ad['creative'] = {'creative_id': creative['id']}
                    ad.remote_create()

                    try:
                        if int(pixel_id) > 0:
                            ad['tracking_specs'] = {
                                'action.type': 'offsite_conversion',
                                'fb_pixel': pixel_id,
                            }
                    except Exception as e:
                        logger.exception(f'Exception: {e}')
                    ad_count = ad_count+1

        ad_batch.execute()

        if not exceptions:
            register_new_ad(creative['id'], fb_account_id, name, campaign_id)

        return response.handler_response(
            200,
            ([], exceptions),
            'Success'
        )

    except FacebookRequestError as e:
        logger.exception(f'FacebookRequestError: {e}')
        msg = ""
        if 'error' in e.body() and 'error_user_msg' in e.body()['error']:
            msg = e.body()['error']['error_user_msg']
        else:
            msg = e.body()['error']['message']
        return response.handler_response(
            400,
            ([], [{"error": msg, "campaign": campaign_id}]),
            'Failed'
        )


def fb_preview_single_image_ad_handler(event, context):
    '''
    Lambda handler for fb_preview_single_image_ad
    '''
    lambda_name = 'fb_preview_single_image_ad'
    logger.info(
        'Received event in fb_preview_single_image_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'instagram_actor_id', 'page_id',
        'call_to_action_type', 'ad_name', 'image', 'ad_copy', 'ad_caption',
        'url', 'link_title', 'ad_description', 'page_actor', 'leadgen_form_id'
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    instagram_actor_id = resp.get('instagram_actor_id')
    call_to_action_type = resp.get('call_to_action_type')
    image = resp.get('image')
    ad_name = resp.get('ad_name')
    ad_copy = resp.get('ad_copy')
    ad_caption = resp.get('ad_caption')
    url = resp.get('url')
    link_title = resp.get('link_title')
    ad_description = resp.get('ad_description')
    page_actor = resp.get('page_actor')
    leadgen_form_id = resp.get('leadgen_form_id')

    res, data = fb_preview_single_image_ad_helper(
        fb_access_token,
        fb_account_id,
        page_id,
        instagram_actor_id,
        call_to_action_type,
        image,
        ad_copy,
        ad_caption,
        url,
        ad_name,
        link_title,
        ad_description,
        page_actor,
        leadgen_form_id,
        "INSTAGRAM_STANDARD"
    )
    if res:
        return response.handler_response(
            200,
            data,
            'Success'
        )
    else:
        return response.handler_response(
            400,
            None,
            data
        )


def fb_create_video_ad_preview_handler(event, context):
    '''
    Lambda handler for fb_create_video_ad_preview
    '''
    lambda_name = 'fb_create_video_ad_preview'
    logger.info(
        'Received event in fb_create_video_ad_preview: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'page_id',
        'ad_name', 'image', 'ad_copy', 'ad_caption',
        'call_to_action_type', 'video_id',
        'url', 'ad_description',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    # instagram_actor_id = resp.get('instagram_actor_id')
    # adset_id_list = resp.get('adset_id_list')
    call_to_action_type = resp.get('call_to_action_type')
    image = resp.get('image')
    ad_name = resp.get('ad_name')
    ad_copy = resp.get('ad_copy')
    ad_caption = resp.get('ad_caption')
    url = resp.get('url')
    # pixel_id = resp.get('pixel_id')
    video_id = resp.get('video_id')
    # campaign_id = resp.get('campaign_id')
    # link_title = resp.get('link_title')
    ad_description = resp.get('ad_description')
    # leadgen_form_name = resp.get('leadgen_form_name')

    try:
        api = fb_api.get_facebook_api(fb_access_token)
        creative_batch = api.new_batch()
        # ad_batch = api.new_batch()
        # ad_list = []
        # ad_id_list = []
        # adset_update_id_list = []
        creative_count = 0
        # creative_list = []
        # ad_count = 0

        with open("/tmp/image.png", "wb") as fd:
            fd.write(image.get_bytes())
        file_image = "/tmp/image.png"

        image = AdImage(parent_id='act_'+str(fb_account_id))
        image[AdImage.Field.filename] = file_image

        image.remote_create()

        if creative_count % 50 == 0:
            logger.info('batch creative')
            creative_batch.execute()
            creative_batch = api.new_batch()

        logger.info('make link')

        video_data = AdCreativeVideoData()
        video_data.update({
            'call_to_action': {
                'type': call_to_action_type,
                'value': {
                    'link': url
                },
            },
        })
        video_data.update({'title': ad_caption})
        video_data.update({'video_id': int(video_id)})
        video_data.update({'image_hash': image[AdImage.Field.hash]})
        video_data.update({'message': ad_copy})
        video_data.update({'link_description': ad_description})

        object_story_spec = ObjectStorySpec()
        object_story_spec.update({'video_data': video_data})
        object_story_spec.update({'page_id': page_id})

        creative2 = AdCreative(parent_id='act_'+str(fb_account_id))
        creative2[AdCreative.Field.name] = ad_name
        creative2['body'] = ad_copy
        creative2['title'] = ad_caption
        creative2[AdCreative.Field.object_story_spec] = object_story_spec
        creative2.remote_create()

        return response.handler_response(
            200,
            {'ad_id': creative2['id']},
            'Success'
        )

    except Exception as e:
        logger.exception(f'Exception: {e}')
        if hasattr(e, 'message'):
            logger.exception(e.message)
            # raise Exception(e.message)
            msg = e['message']
        else:
            # raise Exception(
            #     "Sorry, looks like something went wrong. "
            #     "Please message support for help."
            # )
            msg = (
                "Sorry, looks like something went wrong. "
                "Please message support for help."
            )
        return response.handler_response(
            400,
            None,
            msg
        )


def fb_preview_copy_ad_handler(event, context):
    '''
    Lambda handler for fb_preview_copy_ad
    '''
    lambda_name = 'fb_preview_copy_ad'
    logger.info(
        'Received event in fb_preview_copy_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'ad_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    # fb_account_id = resp.get('fb_account_id')
    ad_id = resp.get('ad_id')

    fb_api.get_facebook_api(fb_access_token)
    ad = Ad(ad_id)
    ad.remote_read(fields=['creative'])

    if 'creative' in ad:
        creative_id = ad['creative']['id']

    return response.handler_response(
        200,
        {'creative_id': creative_id},
        'Success'
    )


def get_html_code_for_ad_preview_instagram_handler(event, context):
    '''
    Lambda handler to get html_code_for_ad_preview_instagram
    '''
    lambda_name = 'get_html_code_for_ad_preview_instagram'
    logger.info(
        'Received event in get_html_code_for_ad_preview_instagram: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'creative_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    creative_id = resp.get('creative_id')

    try:
        fb_api.get_facebook_api(fb_access_token)
        creative = AdCreative(creative_id)

        params = {'ad_format': 'INSTAGRAM_STANDARD', 'summary': 'true'}
        html_code = str(creative.get_previews(params=params)[0]['body'])

        logger.info(f'{html_code=}')

        return response.handler_response(
            200,
            {'html_code': html_code},
            'Success'
        )

    except Exception as e:
        if hasattr(e, 'message'):
            logger.exception(e.message)
            msg = e['message']
        else:
            msg = (
                "Sorry, looks like something went wrong. "
                "Please message support for help."
            )
        return response.handler_response(
            400,
            None,
            msg
        )


def fb_create_post_ad_preview_handler(event, context):
    '''
    Lambda handler for fb_create_post_ad_preview
    '''
    lambda_name = 'fb_create_post_ad_preview'
    logger.info(
        'Received event in fb_create_post_ad_preview: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'page_id', 'post_id_list', 'instagram_id',
        # 'name', 'pixel_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    post_id_list = resp.get('post_id_list')
    instagram_id = resp.get('instagram_id')
    # name = resp.get('name')
    # pixel_id = resp.get('pixel_id')

    try:
        api = fb_api.get_facebook_api(fb_access_token)
        api.new_batch()

        # ad_count = 0
        post_id_list = post_id_list.split(',')

        logger.info(f'{post_id_list=}')

        creative_ids = []
        for post_id in post_id_list:
            logger.info(f'{post_id=}')
            creative = AdCreative(parent_id='act_'+str(fb_account_id))
            creative['name'] = post_id
            creative['object_story_id'] = f'{page_id}_{post_id}'
            if instagram_id > '0':
                creative['instagram_actor_id'] = instagram_id
            try:
                creative.remote_create()
            except Exception as e:
                logger.exception(f'Exception: {e}')
                api = fb_api.get_facebook_api(fb_access_token)
                api.new_batch()
                creative.remote_create()
            logger.info(f"{creative['id']=}")
            creative_ids.append(creative['id'])
        return response.handler_response(
            200,
            {'creative_ids': creative_ids},
            'Success'
        )

    except Exception as e:
        if hasattr(e, 'message'):
            logger.exception(e.message)
            msg = e['message']
        else:
            msg = (
                "Sorry, looks like something went wrong. "
                "Please message support for help."
            )
        return response.handler_response(
            400,
            None,
            msg
        )


def upload_video_ad_handler(event, context):
    '''
    Lambda handler for upload_video_ad
    '''
    lambda_name = 'upload_video_ad'
    logger.info(
        'Received event in upload_video_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'filename',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    filename = resp.get('filename')

    fb_api.get_facebook_api(fb_access_token)

    with open("/tmp/image.mp4", "wb") as fd:
        fd.write(filename.get_bytes())
    file_video = "/tmp/image.mp4"

    video = AdVideo(parent_id='act_'+fb_account_id)
    video[AdVideo.Field.filepath] = file_video
    video.remote_create()

    t = 0
    while t < 60:
        time.sleep(1)
        video.remote_read(fields=['status'])
        if video['status']['video_status'] == 'ready':
            return video['id']
        else:
            if 'processing_progress' in video['status']:
                print(str(video['status']['processing_progress']) + "%")
                logger.info(str(video['status']['processing_progress']) + "%")
            else:
                print(video['status'])
                logger.info(video['status'])
            t += 1
    return response.handler_response(
        200,
        {'video_id': video['id']},
        'Success'
    )


def fb_preview_single_image_ad_newsfeed_handler(event, context):
    '''
    Lambda handler for fb_preview_single_image_ad_newsfeed
    '''
    lambda_name = 'fb_preview_single_image_ad_newsfeed'
    logger.info(
        'Received event in fb_preview_single_image_ad_newsfeed: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_access_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id', 'page_id',
        'ad_name', 'image', 'ad_copy', 'ad_caption',
        'call_to_action_type', 'instagram_actor_id',
        'url', 'ad_description', 'link_title', 'page_actor', 'leadgen_form_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')
    page_id = resp.get('page_id')
    instagram_actor_id = resp.get('instagram_actor_id')
    call_to_action_type = resp.get('call_to_action_type')
    image = resp.get('image')
    ad_name = resp.get('ad_name')
    ad_copy = resp.get('ad_copy')
    ad_caption = resp.get('ad_caption')
    url = resp.get('url')
    page_actor = resp.get('page_actor')
    link_title = resp.get('link_title')
    ad_description = resp.get('ad_description')
    leadgen_form_id = resp.get('leadgen_form_id')

    res, data = fb_preview_single_image_ad_helper(
        fb_access_token,
        fb_account_id,
        page_id,
        instagram_actor_id,
        call_to_action_type,
        image,
        ad_copy,
        ad_caption,
        url,
        ad_name,
        link_title,
        ad_description,
        page_actor,
        leadgen_form_id,
        "MOBILE_FEED_STANDARD"
    )
    if res:
        return response.handler_response(
            200,
            data,
            'Success'
        )
    else:
        return response.handler_response(
            400,
            None,
            data
        )
