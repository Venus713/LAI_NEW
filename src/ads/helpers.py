import time
import datetime

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adimage import AdImage
from facebook_business.specs import LinkData, ObjectStorySpec
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.campaign import Campaign

from utils.logging import logger
from utils.batch import Batch
from utils.constants import AD_FIELDS
from utils.dynamodb import DynamoDb
from utils.facebook import FacebookAPI


pk = 'Ads'
client: DynamoDb = DynamoDb()
fb_api: FacebookAPI = FacebookAPI()


def register_new_ad(ad_id, fb_account_id, ad_name, campaign_id):
    client.create_item(pk, ad_id, {
        'ad_id': ad_id,
        'fb_account_id': fb_account_id,
        'name': ad_name,
        'enabled': True,
        'created_at': str(datetime.datetime.now())
    })
    client.create_item(
        'Campaign_Ad',
        str(campaign_id) + '-' + str(ad_id),
        {
            'campaign_id': campaign_id,
            'ad_id': ad_id
        }
    )


def fb_create_single_image_creative(
    api,
    account_id,
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
):

    filename_time = str(time.time())
    # write the uploaded file to a temp folder to send to FB
    try:
        with open(f'/tmp/{filename_time}.png', 'wb') as fd:
            fd.write(image.get_bytes())
            file_image = f'/tmp/{filename_time}.png'
    except Exception as e:
        logger.exception(f'Exception in fb_create_single_image_creative: {e}')
        logger.info(
            "Looks like you didn't submit an image! "
            "Please upload an image to continue."
        )
        return

    # check the ad account
    account = AdAccount('act_'+str(account_id))
    logger.info(account)

    # create the image
    image = AdImage(parent_id=account['id'])
    image[AdImage.Field.filename] = file_image
    image.remote_create()
    image_hash = image[AdImage.Field.hash]

    # creative_batch = api.new_batch()

    link_data = LinkData()
    link_data[LinkData.Field.name] = link_title
    link_data[LinkData.Field.message] = ad_copy
    link_data[LinkData.Field.link] = url
    link_data[LinkData.Field.caption] = ad_caption
    link_data[LinkData.Field.description] = ad_description
    link_data[LinkData.Field.image_hash] = image_hash

    if deep_link:
        call_to_action = {
                'type': call_to_action_type,
                'value': {
                    'link': url,
                    'app_link ': ad_caption
                }
            }
    else:
        call_to_action = {
            'type': call_to_action_type,
            'value': {
                'link': url
            }
        }

    # add leadgen form if selected
    if int(leadgen_form_id) > 0:
        call_to_action['value'].update({'lead_gen_form_id': leadgen_form_id})

    link_data[LinkData.Field.call_to_action] = call_to_action

    # create object story spec
    object_story_spec = ObjectStorySpec()
    object_story_spec[ObjectStorySpec.Field.page_id] = page_id
    object_story_spec[ObjectStorySpec.Field.link_data] = link_data
    if int(instagram_actor_id) > 0:
        object_story_spec['instagram_actor_id'] = instagram_actor_id

    # create the creative. if the company has an instagram actor ID,
    #  then set instagram ID
    creative = AdCreative(parent_id='act_'+str(account_id))
    creative[AdCreative.Field.name] = ad_name
    creative[AdCreative.Field.object_story_spec] = object_story_spec
    if account_id == '1388855401347764':
        creative['url_tags'] = (
            'utm_medium=ppc&utm_source=Facebook&utm_campaign={{campaign.id}}'
            '&utm_term={{adset.id}}&utm_content={{ad.id}}_{{placement}}'
        )
    elif account_id == '10369968':
        creative['url_tags'] = (
            'try=creativeteams&utm_source=facebook&utm_campaign='
            '{{campaign.id}}&utm_content={{ad.id}}'
        )
    else:
        creative['url_tags'] = (
            'utm_source={{site_source_name}}&utm_campaign={{campaign.id}}'
            '&utm_adset={{adset.id}}&utm_ad={{ad.id}}'
        )

    if int(instagram_actor_id) > 0:
        logger.info('has an insta ID')
        creative[AdCreative.Field.instagram_actor_id] = instagram_actor_id

    exceptions = []
    try:
        creative.remote_create()
    except FacebookRequestError as e:
        logger.info(f'Exeption in fb_create_single_image_creative: {e}')
        exceptions = [e.body()['error']['error_user_msg']]
    logger.info(creative['id'])
    return (creative['id'], exceptions)


def add_ad_to_campaign(api, account_id, campaign_id, ad_creative_id, name):
    # FB part
    acct = AdAccount("act_%d" % int(account_id), api=api)
    campaign = Campaign(campaign_id, api=api)

    ac = AdCreative(ad_creative_id, api=api)
    ac.remote_read(fields=['object_story_spec'])
    logger.info(ac)

    # First, retrieve the ads from the adsets in bulk
    adsets = list(campaign.get_ad_sets())
    logger.info(f'{len(adsets)} adsets')
    samples = []
    with Batch(
        api, results_container=samples, raise_exceptions=True
    ) as batcher:
        for adset in adsets:
            sample = adset.get_ads(
                params={'limit': 1},
                fields=AD_FIELDS,
                batch=batcher.get_batch()
            )
            batcher.add_metadata(adset)

    # Then find the sample ad for each adset.
    samples_by_adset = {}
    base_sample = {}

    for (adset_ads, adset) in samples:
        data = adset_ads['data']
        if data:
            samples_by_adset[adset['id']] = data[0]
            base_sample = data[0]

    # Then make ads like the sample
    successes = []
    failures = []
    with Batch(
        api, results_container=successes, exceptions_container=failures
    ) as batcher:
        for adset in adsets:
            sample = samples_by_adset.get(adset['id'], None)
            if sample is None:
                sample = base_sample
            ad_spec = {}

            if 'id' in ad_spec:
                del ad_spec['id']
            ad_spec['adset_id'] = adset['id']
            ad_spec['creative'] = {'creative_id': ad_creative_id}
            ad_spec['name'] = name
            acct.create_ad(params=ad_spec, batch=batcher.get_batch())

    if len(successes) == 0:
        if len(failures) == 0:
            # raise Exception("No ads to create")
            return False, 'No ads to create'
        else:
            # raise Exception("Those ads could not be added to this campaign")
            return False, 'Those ads could not be added to this campaign'

    else:
        if len(failures) > 0:
            logger.info(
                f'{len(successes)} Succeeded. '
                f'{len(failures)} ads failed to create'
            )
    register_new_ad(ad_creative_id, account_id, name, campaign_id)

    return True, 'Success'


def fb_preview_single_image_ad_helper(
    fb_access_token,
    account_id,
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
    ad_format
):

    # ad_list = []
    # ad_id_list = []
    # adset_update_id_list = []
    # creative_count = 0
    # creative_list = []
    # ad_count = 0
    # write the uploaded file to a temp folder to send to FB
    with open(f'/tmp/{ad_name}.png', 'wb') as fd:
        fd.write((image.get_bytes()))

    file_image = f'/tmp/{ad_name}.png'
    logger.info(file_image)

    fb_api.get_facebook_api(fb_access_token)
    account = AdAccount('act_'+str(account_id))
    logger.info(account)

    # create the image
    image = AdImage(parent_id=account['id'])
    image[AdImage.Field.filename] = file_image
    image.remote_create()
    image_hash = image[AdImage.Field.hash]

    try:
        logger.info(f'{image_hash=}')
        link_data = LinkData()
        link_data[LinkData.Field.name] = link_title
        link_data[LinkData.Field.message] = ad_copy
        link_data[LinkData.Field.link] = url
        link_data[LinkData.Field.caption] = ad_caption
        link_data[LinkData.Field.description] = ad_description
        link_data[LinkData.Field.image_hash] = image_hash

        call_to_action = {
            'type': call_to_action_type,
            'value': {
                'link': url
            }
        }

        # add leadgen form if selected
        if str(leadgen_form_id) > '0':
            try:
                int(leadgen_form_id)
                call_to_action['value'].update(
                    {'lead_gen_form_id': leadgen_form_id}
                )
            except Exception as e:
                logger.exception(f'Exception: {e}')

        link_data[LinkData.Field.call_to_action] = call_to_action

        # create object story spec
        object_story_spec = ObjectStorySpec()
        object_story_spec[ObjectStorySpec.Field.page_id] = page_id
        object_story_spec[ObjectStorySpec.Field.link_data] = link_data

        # create the creative. if the company has an instagram actor ID,
        #  then set instagram ID
        creative = AdCreative(parent_id='act_'+str(account_id))
        creative[AdCreative.Field.name] = ad_name
        creative[AdCreative.Field.object_story_spec] = object_story_spec

        try:
            if int(instagram_actor_id) > 0:
                creative[AdCreative.Field.instagram_actor_id] = (
                    instagram_actor_id
                )
        except Exception as e:
            logger.exception(f'Exception: {e}')
        creative.remote_create()

        if page_actor:
            creative.remote_read(
                fields=[AdCreative.Field.use_page_actor_override]
            )
            creative['use_page_actor_override'] = 'true'
            creative.remote_update()

        params = {'ad_format': ad_format, 'summary': 'true'}

        html_code = str(creative.get_previews(params=params)[0]['body'])

        print(html_code)

        return True, {'html_code': html_code}

    except Exception as e:
        if 'message' in e:
            # raise Exception(e['message'])
            return False, e['message']
        else:
            logger.exception(f'Exception: {e}')
            # raise Exception(
            #     "Sorry, looks like something went wrong."
            #     "Please message support for help."
            # )
            return False, (
                "Sorry, looks like something went wrong."
                "Please message support for help."
            )
