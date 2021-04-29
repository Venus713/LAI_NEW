import os

from facebook_business import FacebookAdsApi
from facebook_business.adobjects.user import User

from .logging import logger


class FacebookAPI:

    def __init__(self):
        self.app_id = os.environ.get('APP_ID')
        self.app_secret = os.environ.get('APP_SECRET')
    
    def get_facebook_api(self, fb_access_token):
        try:
            return FacebookAdsApi.init(
                self.app_id,
                self.app_secret,
                fb_access_token
            )
        except Exception as e:
            logger.error(
                f'Raised error in get_facebook_api: {e}'
            )
            raise Exception(
                'Could not connect to the Facebook API with this user')

    def get_account_name_list(self, token):
        api = self.get_facebook_api(token)

        try:
            accounts = User(
                fbid='me', api=api).get_ad_accounts(fields=['name', 'id'])

            if len(accounts) > 0:
                account_list = [(
                    account['name'],
                    account['id'][4:]
                ) for account in accounts]
                accounts_sorted = sorted(
                    account_list,
                    key=lambda account: account[0]
                )
            else:
                accounts_sorted = [('', 0)]

            return accounts_sorted
        except Exception as e:
            logger.error(
                f'Raised error in get_account_name_list: {e}'
            )
            raise Exception("Can't connect to Facebook account")

    def get_page_list(self, token):
        api = self.get_facebook_api(token)
        try:
            pages = User(
                fbid='me', api=api).get_accounts(fields=['name', 'id'])
            page_list = [
                (page['name'], page['id']) for page in pages if 'name' in page
            ]
            if page_list:
                pages_sorted = sorted(page_list, key=lambda page: page[0])
            else:
                pages_sorted = [('', 0)]

            return pages_sorted
        except Exception as e:
            logger.error(
                f'Raised error in get_page_list: {e}'
            )
            raise Exception("Can't connect to Facebook account")
