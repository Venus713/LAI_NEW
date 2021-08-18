import json
import datetime
import os
import base64

from utils.logging import logger
from utils.event_parser import EventParser
from utils.cognito import Cognito
from utils.s3 import S3Client
from utils.dynamodb import DynamoDb
from utils.auth import Authentication
from utils.response import Response
from utils.facebook import FacebookAPI

pk = 'User'
user_roles = ('customer', 'admin',)

event_parser: EventParser = EventParser()
cognito: Cognito = Cognito()
s3_client: S3Client = S3Client()
client: DynamoDb = DynamoDb()
auth: Authentication = Authentication()
response: Response = Response()
fb_api: FacebookAPI = FacebookAPI()


def signup(event, context):
    '''
    signup handler
    '''
    lambda_name: str = 'signup'

    logger.info(
        f'Received event in signup: {json.dumps(event, indent=2)}')

    body_required_field = ('username', 'email', 'password', 'role')
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp['email']
    password = resp['password']

    signup_resp, usr_data = cognito.sign_up(email, password)

    if signup_resp['statusCode'] == 200:
        item = {
            'user_id': usr_data['UserSub'],
            'confirm_status': usr_data['UserConfirmed'],
            'last_modified_date': str(datetime.datetime.now()),
            'is_disabled': False
        }
        resp.update(item)
        sk = usr_data['UserSub']
        create_resp = client.create_item(pk, sk, resp)
        logger.info(f'response in sign_up: {create_resp}')
    return signup_resp


def custom_message(event, context):
    logger.info(
        f'Received event in custom_message: {json.dumps(event, indent=2)}')

    if event['triggerSource'] == 'CustomMessage_SignUp':
        code = event['request']['codeParameter']
        # link = event['request']['linkParameter']
        client_id = event['callerContext']['clientId']
        email = event['request']['userAttributes']['email']
        user_id = event['userName']
        callback_url = os.environ['CALL_BACK_URL']
        url = (callback_url + '/userEmailVerification' +
               f'/?code={code}&user_id={user_id}' +
               f'&clientId={client_id}&email={email}')
        event['response']['emailSubject'] = 'Please verify your email address'
        event['response']['emailMessage'] = (
            f'To verify your email address, Please cline this link: {url}.'
        )
    return event


def confirm_signup(event, context):
    '''
    handler for user confirm_signup
    '''
    lambda_name: str = 'confirm_signup'

    logger.info(
        f'Received event in confirm_signup: {json.dumps(event, indent=2)}')

    body_required_field = ('email', 'code', 'user_id')
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp['email']
    code = resp['code']
    user_id = resp['user_id']

    confirm_signup_resp = cognito.confirm_sign_up(code, email)
    if confirm_signup_resp.get('statusCode') == 200:
        item = {
            'confirm_status': True,
            'last_modified_date': str(datetime.datetime.now())
        }
        resp = client.update_item(pk, user_id, item)
        logger.info(f'update_item response in confirm_signup: {resp}')
    return confirm_signup_resp


def confirm_facebook(event, context):
    '''
    handler for user facebook auth
    '''
    lambda_name: str = 'confirm_fb'

    logger.info(
        f'Received event in confirm_fb: {json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)

    if auth_res is False:
        return response.auth_failed_response()

    body = json.loads(event['body'])
    body_required_field = ('user_id', 'fb_access_token',)

    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    user_id = resp['user_id']
    fb_access_token = resp['fb_access_token']
    logger.info(f'fb_access_token: {fb_access_token}')

    # ====== check if user_id deos exist in db ====== #
    user_info = client.get_item(pk, user_id)
    logger.info(f'response of user_retrieve in confirm_fb: {user_info}')
    if not user_info:
        return response.not_found_exception_response('user_id')

    account_list = fb_api.get_account_name_list(fb_access_token)
    logger.info(f'account_list in confirm_fb: {account_list}')

    for account in account_list:
        fb_account_id = int(account[1])
        fb_account_name = account[0].replace("'", "")

        user_fb_info = {
            'user_email': user_info['email'],
            'fb_access_token': fb_access_token,
            'fb_page_id': '',
            'fb_instagram_id': '',
            'fb_pixel_id': '',
            'fb_app_id': '',
            'fb_account_id': fb_account_id,
            'name': fb_account_name,
            'account_type': 'facebook',
            'credit_plan': '',
            'spend_credits_left': 0
        }
        sk1 = str(fb_account_id) + '-' + str(user_id)
        # sk2 = str(user_id) + '-' + str(fb_account_id)
        client.create_item('FB_Account', sk1, user_fb_info)
        # client.create_item('FB_Account', sk2, user_fb_info)

    user_info.update({
        'is_onboarding_complete': True,
        'fb_access_token': fb_access_token
    })
    user_info.pop('sk')
    user_info.pop('pk')
    resp = client.update_item(pk, user_id, user_info)
    logger.info(f'update_item response in confirm_fb: {resp}')

    return response.handler_response(
        200, body, 'Successfully completed facebook auth!')


def resend_verification_code(event, context):
    '''
    handler for resend_verification_code
    '''
    lambda_name: str = 'resend_verification_code'

    logger.info(
        f'Received event in resend_verify_code: {json.dumps(event, indent=2)}')

    body_required_field = ('email',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return response
    email = resp['email']

    resend_code_resp = cognito.resend_verification_code(email)
    logger.info(f'response in resend_verify_code: {resend_code_resp}')
    return resend_code_resp


def signin(event, context):
    '''
    handler for user signin
    '''
    lambda_name: str = 'signin'

    logger.info(
        f'Received event in signin: {json.dumps(event, indent=2)}')

    body_required_field = ('email', 'password',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp['email']
    password = resp['password']

    usr_resp = client.query_item(pk, {'email': email})
    logger.info(f'query_item response in sign_in: {usr_resp}')

    if not usr_resp:
        return response.build_response(
            400,
            None,
            'User does not exist.'
        )
    signin_resp = cognito.sign_in(email, password, usr_resp[0])

    if signin_resp.get('statusCode') == 200:
        attr_body = {
            'last_modified_date': str(datetime.datetime.now())
        }
        user_id = usr_resp[0]['user_id']
        user_resp = client.update_item(pk, user_id, attr_body)
        logger.info(f'update_item response in sign_in: {user_resp}')

    return signin_resp


def sign_out(event, context):
    '''
    handler for user sign_out
    '''
    lambda_name: str = 'sign_out'

    logger.info(
        f'Received event in sign_out: {json.dumps(event, indent=2)}')

    header_required_field = ('Access-Token',)
    resp, res = event_parser.get_params(
        lambda_name, 'headers', event, header_required_field)
    if res is False:
        return resp
    access_token = resp['Access-Token']

    resp = cognito.global_signout(access_token)
    return resp


def check_token(event, context):
    """
    handler for checking if Access-Token is valid
    """
    lambda_name: str = 'check_token'

    logger.info(
        'Received event in check_token: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.handler_response(
            200,
            None,
            'AccessToken is Invalid.'
        )

    usr_resp = client.query_item(pk, {'user_id': user_id})
    return response.handler_response(
        200,
        usr_resp,
        'AccessToken is valid.'
    )


def changepassword(event, context):
    '''
    handler for changepassword
    '''
    lambda_name: str = 'changepassword'

    logger.info(
        f'Received event in changepassword: {json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    body_required_field = ('previous_pass', 'proposed_pass', 'email',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    previous_pass = resp['previous_pass']
    proposed_pass = resp['proposed_pass']
    email = resp['email']

    resp = cognito.change_password(
        previous_pass, proposed_pass, event['headers']['Access-Token'], email
    )

    return resp


def forgotpassword(event, context):
    '''
    handler for forgotpassword
    '''
    lambda_name: str = 'forgotpassword'

    logger.info(
        f'Received event in forgotpassword: {json.dumps(event, indent=2)}')

    body_required_field = ('email',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp['email']

    resp = cognito.forgot_password(email)
    logger.info(f'response in forgotpassword: {resp}')
    return resp


def confirm_forgotpassword(event, context):
    '''
    handler for confirm_forgotpassword
    '''
    lambda_name: str = 'confirm_forgotpassword'

    logger.info(
        'Received event in confirm_forgotpassword: ' +
        f'{json.dumps(event, indent=2)}')

    body_required_field = ('email', 'password', 'code',)
    resp, res = event_parser.get_params(
        lambda_name, 'body', event, body_required_field)
    if res is False:
        return resp
    email = resp['email']
    password = resp['password']
    code = resp['code']

    resp = cognito.confirm_forgot_password(code, email, password)
    logger.info(f'response in confirm_forgotpassword: {resp}')
    return resp


def userlist(event, context):
    '''
    handler for userlist
    '''
    lambda_name: str = 'userlist'

    logger.info(
        'Received event in userlist: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    if role == 'admin':
        resp = client.query_item(pk, {'is_disabled': False})
        logger.info(f'response in userlist: {resp}')
        return response.handler_response(
            200,
            resp,
            'successfully retrieved all users'
        )
    else:
        return response.build_response(
            400, None, 'Maybe you do not have an admin permission')


def retrieve_user(event, context):
    '''
    handler for retrieve_user
    '''
    lambda_name: str = 'retrieve_user'

    logger.info(
        'Received event in retrieve_user: ' +
        f'{json.dumps(event, indent=2)}')

    req_id = event['pathParameters']['id']

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    if role == 'admin':
        # resp = client.query_item(pk, {'user_id': req_id})
        resp = client.get_item(pk, req_id)
        logger.info(f'response in user_retrieve: {resp}')
        return response.handler_response(
            200,
            resp,
            'successfully retrieved'
        )
    elif user_id == req_id:
        resp = client.get_item(pk, req_id)
        logger.info(f'response in retrieve_user: {resp}')
        return response.handler_response(
            200,
            resp,
            'successfully retrieved'
        )

    return response.build_response(400, None, 'Failed in retrieve user')


def update_user(event, context):
    '''
    handler for update a user
    '''
    lambda_name: str = 'update_user'

    logger.info(
        'Received event in updating a user: ' +
        f'{json.dumps(event, indent=2)}')

    req_id = event['pathParameters']['id']

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    # available_field = (
    #     'real_name', 'is_paid', 'is_onboard_complete',
    #     'plan', 'role', 'max_ads', 'current_ads', 'company_name',
    #     'company_url', 'company_industry', 'company_role', 'strip_id',
    # )

    body = json.loads(event['body'])
    for key, val in body.items():
        if key == 'role':
            req_role = val
            if req_role not in user_roles:
                return response.build_response(
                    400, None, 'Provided invalid role')
        if key == 'email':
            return response.build_response(
                    400, None, 'You can not change the email.')

    if role == 'admin':
        attr_resp = {
            'last_modified_date': str(datetime.datetime.now())
        }
        body.update(attr_resp)
        logger.info(f'Updated resp in update handler: {body}')

        resp = client.update_item(pk, req_id, body)
        logger.info(f'response in update handler: {resp}')
        return response.handler_response(
            200,
            resp,
            'successfully updated'
        )
    elif req_id == user_id:
        if body.get('photo'):
            photo = body['photo']
            photo = photo[photo.find(',')+1:]
            dec_photo = base64.b64decode(photo + '==')
            photo_url = s3_client.image_upload(pk, user_id, dec_photo)
            attr_resp = {
                'last_modified_date': str(datetime.datetime.now()),
                'photo': photo_url
            }
        else:
            attr_resp = {
                'last_modified_date': str(datetime.datetime.now())
            }
        body.update(attr_resp)
        body['role'] = user_roles[0]
        logger.info(f'Updated resp in update handler: {body}')

        resp = client.update_item(pk, req_id, body)
        logger.info(f'response in update handler: {resp}')
        return response.handler_response(
            200,
            resp,
            'successfully updated'
        )
    elif auth_res is False:
        return response.auth_failed_response()
    return response.build_response(400, None, 'Failed in update user')


def delete_user(event, context):
    '''
    handler for deleting a user
    '''
    lambda_name: str = 'user_delete'

    logger.info(
        'Received event in deleting a user: ' +
        f'{json.dumps(event, indent=2)}')

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()
    header_required_field = ('Access-Token',)
    params, res = event_parser.get_params(
        lambda_name, 'headers', event, header_required_field)
    access_token = params['Access-Token']

    delete_res = cognito.delete_user(user_id, access_token)
    if delete_res.get('statusCode') == 200:
        resp = client.delete_item(pk, user_id)
        logger.info(f'response in deleting a user: {resp}')

    return delete_res


def disable_user(event, context):
    '''
    handler for disable a user
    '''
    lambda_name: str = 'user_disable'

    logger.info(
        'Received event in deleting a user: ' +
        f'{json.dumps(event, indent=2)}')

    body = json.loads(event['body'])

    req_id = event['pathParameters']['id']

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    if role == 'admin':
        disable_res = cognito.admin_disable_user(req_id)
        if disable_res.get('statusCode') == 200:
            attr_resp = {
                'is_disabled': True,
                'last_modified_date': str(datetime.datetime.now())
            }
            body.update(attr_resp)

            resp = client.update_item(pk, req_id, body)
            logger.info(f'response in deleting a user: {resp}')
            return disable_res
        return disable_res
    else:
        return response.build_response(
            400, None, 'Failded disable_user')


def enable_user(event, context):
    '''
    handler for enable a user
    '''
    lambda_name: str = 'user_enable'

    logger.info(
        'Received event in enable a user: ' +
        f'{json.dumps(event, indent=2)}')

    body = json.loads(event['body'])

    req_id = event['pathParameters']['id']

    auth_res, role, user_id = auth.get_auth(lambda_name, event)
    if auth_res is False:
        return response.auth_failed_response()

    if role == 'admin':
        enable_res = cognito.admin_enable_user(req_id)
        if enable_res:
            attr_resp = {
                'is_disabled': False,
                'last_modified_date': str(datetime.datetime.now())
            }
            body.update(attr_resp)

            resp = client.update_item(pk, req_id, body)
            logger.info(f'response in enable a user: {resp}')
            return enable_res
        return enable_res
    else:
        return response.build_response(
            400, None, 'Failded enable_user')
