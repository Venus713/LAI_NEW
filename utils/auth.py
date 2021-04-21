import json
from .dynamodb import DynamoDb
from .cognito import Cognito
from .logging import logger
from .event_parser import EventParser

event_parser: EventParser = EventParser()


class Authentication:
    access_token: str = ''
    pk: str = 'User'

    def __init__(self):
        self.__dynamodb = DynamoDb()
        self.__cognito = Cognito()

    def is_auth(self, access_token: str):
        logger.info(
            f'Received access_token in is_auth: {access_token}')
        user_resp = self.__cognito.get_user(access_token)
        logger.info(
            f'cognito_user_resp from access_token in is_auth: {user_resp}')

        if user_resp.get('statusCode') == 200:
            user_id = json.loads(user_resp.get('body')).get('data')
            print('===============================')
            print(f'{user_id=}')
            user_info = self.__dynamodb.query_item(
                self.pk, {'user_id': user_id})
            logger.info(
                f'dynamodb userinfo from access_token in is_auth: {user_info}')
            if user_info:
                logger.info('user auth is success.')
                return True, user_info[0].get('role'), user_id
            else:
                logger.info(
                    'user auth is success, but does not have profile')
                return True, None, user_id
        else:
            logger.info('user auth failed.')
            return False, None, None

    def get_auth(self, lambda_name: str, event: dict):
        header_required_field = ('Access-Token',)
        resp, res = event_parser.get_params(
            lambda_name, 'headers', event, header_required_field)
        if res is False:
            return resp, None, None
        access_token = resp['Access-Token']
        logger.info(
            f'Received Access-Token in {lambda_name} handler: ' +
            f'{json.dumps(event, indent=2)}')

        auth_res, usr_role, usr_id = self.is_auth(access_token)
        return auth_res, usr_role, usr_id
