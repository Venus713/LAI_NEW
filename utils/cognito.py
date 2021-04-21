import os
import boto3

from .logging import logger
from .response import Response


class Cognito:
    token: str = ''
    user_pool_id: str = ''
    user_pool_client_id: str = ''
    client_secret: str = ''

    def __init__(self):
        self.__client = boto3.client(
            'cognito-idp', region_name=os.environ['APP_REGION'])
        self.__user_pool_id = os.environ['USER_POOL_ID']
        self.__user_pool_client_id = os.environ['USER_POOL_CLIENT_ID']
        self.response = Response()

    def initiate_auth(self, username, password):
        resp = self.__client.initiate_auth(
            ClientId=self.__user_pool_client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
            },
            ClientMetadata={
                'username': username,
                'password': password,
            }
        )
        return resp

    def sign_in(self, email: str, password: str, data: dict):
        try:
            resp = self.initiate_auth(email, password)
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.UserNotConfirmedException:
            return self.response.user_not_confirmed_exception_response(email)
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response()
        except self.__client.exceptions.InvalidUserPoolConfigurationException:
            return self.response.invalid_user_pool_config_exception_response()
        except self.__client.exceptions.UserLambdaValidationException:
            return self.response.user_lambda_validation_exception_response()
        except self.__client.exceptions.InvalidLambdaResponseException:
            return self.response.invalid_lambda_response_exception_response()
        except self.__client.exceptions.PasswordResetRequiredException:
            return self.response.password_reset_required_exception_response()
        except self.__client.exceptions.UserNotFoundException:
            return self.response.user_not_found_exception_response(email)
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except self.__client.exceptions.InvalidSmsRoleAccessPolicyException:
            return (
                self.response.invalid_sms_role_access_policy_excep_response()
            )
        except (
            self.__client.exceptions.InvalidSmsRoleTrustRelationshipException
        ):
            return (
                self.response.invalid_sms_role_trust_relation_expt_response()
            )
        except Exception as e:
            return self.response.exception_response(e)

        if resp.get('AuthenticationResult'):
            body = {
                'id_token': resp['AuthenticationResult']['IdToken'],
                'refresh_token': resp['AuthenticationResult']['RefreshToken'],
                'access_token': resp['AuthenticationResult']['AccessToken'],
                'expires_in': resp['AuthenticationResult']['ExpiresIn'],
                'token_type': resp['AuthenticationResult']['TokenType'],
                'email': email
            }
            body.update(data)
            return self.response.handler_response(
                200,
                body,
                'success'
            )
        else:
            return self.response.signin_failed_response()

    def sign_up(self, email: str, password: str):
        try:
            resp = self.__client.sign_up(
                ClientId=self.__user_pool_client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    }
                ],
                ValidationData=[
                    {
                        'Name': 'email',
                        'Value': email
                    }
                ]
            )
            logger.info(
                f'user signup response: {resp}'
            )
        except self.__client.exceptions.UsernameExistsException:
            return self.response.exist_exception_response(email), {}
        except self.__client.exceptions.InvalidPasswordException:
            return self.response.invalid_password_exception_response(), {}
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response(), {}
        except self.__client.exceptions.UserNotConfirmedException:
            return self.response.user_not_confirmed_exception_response(email)
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response(), {}
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response(), {}
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response(), {}

        except self.__client.exceptions.UserLambdaValidationException:
            return (
                self.response.user_lambda_validation_exception_response(), {}
            )
        except self.__client.exceptions.InvalidLambdaResponseException:
            return (
                self.response.invalid_lambda_response_exception_response(), {}
            )
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response(), {}
        except self.__client.exceptions.InvalidSmsRoleAccessPolicyException:
            return (
                self.response.invalid_sms_role_access_policy_excep_response(),
                {}
            )
        except (
            self.__client.exceptions.InvalidSmsRoleTrustRelationshipException
        ):
            return (
                self.response.invalid_sms_role_trust_relation_expt_response(),
                {}
            )
        except (
            self.__client.exceptions.InvalidEmailRoleAccessPolicyException
        ):
            return (
                self.response.invalid_email_role_access_policy_expt_response(),
                {}
            )
        except Exception as e:
            return self.response.exception_response(e), {}
        return self.response.signup_response(resp), resp

    def confirm_sign_up(self, code: str, email: str) -> dict:
        try:
            resp = self.__client.confirm_sign_up(
                ClientId=self.__user_pool_client_id,
                Username=email,
                ConfirmationCode=code,
                ForceAliasCreation=False
            )
            logger.info(
                f'user confirm_signup response: {resp}'
            )
        except self.__client.exceptions.UserNotFoundException:
            return self.response.not_found_exception_response(email)
        except self.__client.exceptions.CodeMismatchException:
            return self.response.invalid_confirmcode_exception_response(code)
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response()
        except self.__client.exceptions.UserLambdaValidationException:
            return self.response.user_lambda_validation_exception_response()
        except self.__client.exceptions.InvalidLambdaResponseException:
            return self.response.invalid_lambda_response_exception_response()
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except self.__client.exceptions.TooManyFailedAttemptsException:
            return self.response.too_many_failed_attempts_except_response()
        except self.__client.exceptions.ExpiredCodeException:
            return self.response.expired_code_except_response()
        except self.__client.exceptions.AliasExistsException:
            return self.response.alias_exists_except_response()
        except self.__client.exceptions.LimitExceededException:
            return self.response.limit_exceeded_except_response()
        except Exception as e:
            return self.response.exception_response(e)

        return self.response.handler_response(
            200,
            {'email': email},
            'successfully confirmed'
        )

    def resend_verification_code(self, email):
        try:
            resp = self.__client.resend_confirmation_code(
                ClientId=self.__user_pool_client_id,
                Username=email,
            )
            logger.info(
                f'resend_verification_code response: {resp}'
            )
        except self.__client.exceptions.UserNotFoundException:
            return self.response.not_found_exception_response(email)
        except self.__client.exceptions.InvalidParameterException:
            return self.response.already_confirm_exception_response(email)
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response()
        except self.__client.exceptions.UserLambdaValidationException:
            return self.response.user_lambda_validation_exception_response()
        except self.__client.exceptions.InvalidLambdaResponseException:
            return self.response.invalid_lambda_response_exception_response()
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()

        except self.__client.exceptions.LimitExceededException:
            return self.response.limit_exceeded_except_response()
        except self.__client.exceptions.InvalidSmsRoleAccessPolicyException:
            return (
                self.response.invalid_sms_role_access_policy_excep_response(),
                {}
            )
        except (
            self.__client.exceptions.InvalidSmsRoleTrustRelationshipException
        ):
            return (
                self.response.invalid_sms_role_trust_relation_expt_response()
            )
        except (
            self.__client.exceptions.InvalidEmailRoleAccessPolicyException
        ):
            return (
                self.response.invalid_email_role_access_policy_expt_response()
            )
        except Exception as e:
            return self.response.exception_response(e)

        return self.response.handler_response(
            200, email, 'resent a verification_code'
        )

    def forgot_password(self, email):
        try:
            resp = self.__client.forgot_password(
                ClientId=self.__user_pool_client_id,
                Username=email
            )
            logger.info(
                f'forgot_password response: {resp}'
            )
        except self.__client.exceptions.UserNotFoundException:
            return self.response.not_found_exception_response(email)
        except self.__client.exceptions.UserNotConfirmedException:
            return self.response.user_not_confirmed_exception_response(email)
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response()
        except self.__client.exceptions.UserLambdaValidationException:
            return self.response.user_lambda_validation_exception_response()
        except self.__client.exceptions.InvalidLambdaResponseException:
            return self.response.invalid_lambda_response_exception_response()
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except self.__client.exceptions.LimitExceededException:
            return self.response.limit_exceeded_except_response()
        except self.__client.exceptions.InvalidSmsRoleAccessPolicyException:
            return (
                self.response.invalid_sms_role_access_policy_excep_response(),
                {}
            )
        except (
            self.__client.exceptions.InvalidSmsRoleTrustRelationshipException
        ):
            return (
                self.response.invalid_sms_role_trust_relation_expt_response()
            )
        except (
            self.__client.exceptions.InvalidEmailRoleAccessPolicyException
        ):
            return (
                self.response.invalid_email_role_access_policy_expt_response()
            )
        except Exception as e:
            return self.response.exception_response(e)
        return self.response.handler_response(
            200,
            email,
            'Please check your email for validation code'
        )

    def confirm_forgot_password(self, code, email, password):
        try:
            self.__client.confirm_forgot_password(
                ClientId=self.__user_pool_client_id,
                Username=email,
                ConfirmationCode=code,
                Password=password
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.UnexpectedLambdaException:
            return self.response.unexpected_lambda_exception_response()
        except self.__client.exceptions.UserLambdaValidationException:
            return self.response.user_lambda_validation_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.CodeMismatchException:
            return self.response.invalid_confirmcode_exception_response(code)
        except self.__client.exceptions.ExpiredCodeException:
            return self.response.expired_code_except_response()
        except self.__client.exceptions.TooManyFailedAttemptsException:
            return self.response.too_many_failed_attempts_except_response()
        except self.__client.exceptions.InvalidLambdaResponseException:
            return self.response.invalid_lambda_response_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.LimitExceededException:
            return self.response.limit_exceeded_except_response()
        except self.__client.exceptions.UserNotFoundException:
            return self.response.not_found_exception_response(email)
        except self.__client.exceptions.UserNotConfirmedException:
            return self.response.user_not_confirmed_exception_response(email)        
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            return self.response.exception_response(e)
        return self.response.handler_response(
            200,
            email,
            'Password has been changed successfully'
        )

    def change_password(
        self, oldpass: str, newpass: str, token: str, email: str
    ):
        try:
            self.__client.change_password(
                PreviousPassword=oldpass,
                ProposedPassword=newpass,
                AccessToken=token
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.InvalidPasswordException:
            return self.response.invalid_password_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.LimitExceededException:
            return self.response.limit_exceeded_except_response()
        except self.__client.exceptions.PasswordResetRequiredException:
            return self.response.password_reset_required_exception_response()
        except self.__client.exceptions.UserNotFoundException:
            return self.response.not_found_exception_response(email)
        except self.__client.exceptions.UserNotConfirmedException:
            return self.response.user_not_confirmed_exception_response(email)
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            return self.response.exception_response(e)

        return self.response.build_response(
            200, None, 'Successfully password changed')

    def global_signout(self, access_token: str) -> bool:
        try:
            resp = self.__client.global_sign_out(
                AccessToken=access_token
            )
            logger.info(
                f'response in global_sign_out: {resp}'
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.PasswordResetRequiredException:
            return self.response.password_reset_required_exception_response()  
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            return self.response.exception_response(e)
        return self.response.handler_response(
            200, None, 'Successfully signing out')

    def get_user(self, access_token: str):
        try:
            resp = self.__client.get_user(
                AccessToken=access_token
            )
            logger.info(
                f'authentication response: {resp}'
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.PasswordResetRequiredException:
            return self.response.password_reset_required_exception_response()   
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            logger.info(
                Exception(
                    f'Unknown error {e.__str__()}'
                )
            )
            return self.response.auth_failed_response()
        username = resp.get('Username', '')
        return self.response.build_response(200, username, '')

    def admin_disable_user(self, username: str) -> bool:
        try:
            self.__client.admin_disable_user(
                UserPoolId=self.__user_pool_id,
                Username=username
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UserNotFoundException:
            return self.response.user_not_found_exception_response(username)
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            return self.response.exception_response(e)
        return self.response.build_response(
            200, {'user_id': username}, 'Successfully disabled')

    def admin_enable_user(self, username: str) -> bool:
        try:
            self.__client.admin_enable_user(
                UserPoolId=self.__user_pool_id,
                Username=username
            )
        except self.__client.exceptions.ResourceNotFoundException:
            return self.response.resource_not_found_exception_response()
        except self.__client.exceptions.InvalidParameterException:
            return self.response.invalid_parameter_exception_response()
        except self.__client.exceptions.NotAuthorizedException:
            return self.response.not_authorized_exception_response()
        except self.__client.exceptions.TooManyRequestsException:
            return self.response.too_many_requests_exception_response()
        except self.__client.exceptions.UserNotFoundException:
            return self.response.user_not_found_exception_response(username)
        except self.__client.exceptions.InternalErrorException:
            return self.response.internal_error_exception_response()
        except Exception as e:
            return self.response.exception_response(e)
        return self.response.build_response(
            200, {'user_id': username}, 'Successfully enabled')
