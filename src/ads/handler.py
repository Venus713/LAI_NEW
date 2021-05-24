import json
from collections import defaultdict

from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.adaccount import AdAccount

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
    fb_account_token = user_info.get('fb_access_token')

    body_required_field = (
        'creative_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    creative_id = resp.get('creative_id')

    try:
        fb_api.get_facebook_api(fb_account_token)
        creative = AdCreative(creative_id)

        params = {'ad_format': 'DESKTOP_FEED_STANDARD', 'summary': 'true'}
        html_code = str(creative.get_previews(params=params)[0]['body'])

        logger.info(html_code)

        return response.handler_response(
            200,
            html_code,
            'Success'
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
    Lambda handler to import import_ad
    '''
    lambda_name = 'import_ad'
    logger.info(
        'Received event in import_ad: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    user_info = client.get_item('User', user_id)
    fb_account_token = user_info.get('fb_access_token')

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
        api = fb_api.get_facebook_api(fb_account_token)
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
    fb_account_token = user_info.get('fb_access_token')

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

    fb_api.get_facebook_api(fb_account_token)
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
    fb_account_token = user_info.get('fb_access_token')

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
    api = fb_api.get_facebook_api(fb_account_token)
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
    fb_account_token = user_info.get('fb_access_token')

    api = fb_api.get_facebook_api(fb_account_token)
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
    fb_account_token = user_info.get('fb_access_token')

    body_required_field = (
        'page_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    page_id = resp.get('page_id')

    try:
        fb_api.get_facebook_api(fb_account_token)

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
    fb_account_token = user_info.get('fb_access_token')

    body_required_field = (
        'fb_account_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    fb_account_id = resp.get('fb_account_id')

    try:
        fb_api.get_facebook_api(fb_account_token)
        account = AdAccount('act_'+str(fb_account_id))
        ad_list = list(make_request(
            account.get_ads, fields=['id', 'name'], params={'limit': 200}
        ))

        ad_list_by_adset = defaultdict(list)
        i = 0
        for ad in ad_list:
            if i % 500 == 0:
                print(ad, i)
            ad_list_by_adset[ad['adset_id']].append(ad['name'])
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


def get_insta_page_id(event, context):
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
    fb_account_token = user_info.get('fb_access_token')

    body_required_field = (
        'page_id',
    )
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    page_id = resp.get('page_id')

    try:
        fb_api.get_facebook_api(fb_account_token)
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
            'Failed'
        )

    except Exception as e:
        return response.handler_response(
            400,
            None,
            f'Raised Exception in get_insta_page_id: {e}'
        )
