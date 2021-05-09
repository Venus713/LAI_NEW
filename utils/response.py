import json
from typing import Any

from .logging import logger


class Response:

    def build_response(self, status_code: Any, body: Any, msg: str) -> dict:
        logger.info(
            'Returned resp body in build_response: ' +
            f'{json.dumps(body, indent=2)}')
        return {
            'statusCode': status_code,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            'body': json.dumps({
                'data': body,
                'message': msg
            })
        }

    def handler_response(self, code: Any, body: Any, msg) -> dict:
        return self.build_response(code, body, msg)

    def not_found_param_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'{key} is required'
            )
        )
        return self.build_response(
            400,
            None,
            f'{key} is required'
        )

    def exception_response(self, e: Any) -> dict:
        logger.error(
            Exception(
                f'Unknown error {e.__str__()}'
            )
        )
        return self.build_response(
            400,
            None,
            f'Unknown error {e.__str__()}'
        )

    def signup_response(self, body) -> dict:
        logger.info(
            'Please confirm your signup, check Email for validation code'
        )
        return self.build_response(
            200,
            body,
            'Please confirm your signup, check Email for validation code'
        )

    def confirmsignup_response(self) -> dict:
        logger.info('Successfully registered')
        return self.build_response(
            200,
            None,
            'Successfully registered'
        )

    def signin_failed_response(self) -> dict:
        logger.error(
            Exception(
                'signin falied'
            )
        )
        return self.build_response(
            401,
            None,
            'signin falied'
        )

    def auth_failed_response(self) -> dict:
        logger.error(
            Exception(
                'Invalid Access Token'
            )
        )
        return self.build_response(
            401,
            None,
            'Invalid Access Token'
        )

    def not_authorized_exception_response(self) -> dict:
        logger.error(
            Exception(
                'NotAuthorizeException: Incorrect username or password'
            )
        )
        return self.build_response(
            401,
            None,
            'Incorrect username or password'
        )

    def exist_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'{key} already exists!'
            )
        )
        return self.build_response(
            409,
            None,
            f'{key} already exists!'
        )

    def not_found_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'{key} does not exists!'
            )
        )
        return self.build_response(
            404,
            None,
            f'{key} does not exists!'
        )

    def invalid_password_exception_response(self) -> dict:
        logger.error(
            Exception(
                'Password should have Caps, Special chars, Numbers'
            )
        )
        return self.build_response(
            400,
            None,
            'Password should have Caps, Special chars, Numbers'
        )

    def invalid_confirmcode_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'{key}: Invalid Verification code'
            )
        )
        return self.build_response(
            404,
            None,
            f'{key}: Invalid Verification code'
        )

    def already_confirm_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'{key} is already confirmed'
            )
        )
        return self.build_response(
            400,
            None,
            f'{key} is already confirmed'
        )

    def user_not_confirmed_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'UserNotConfirmedException: {key} is not confirmed'
            )
        )
        return self.build_response(
            401,
            None,
            f'{key} is not confirmed'
        )

    def resource_not_found_exception_response(self) -> dict:
        logger.error(
            Exception(
                'ResourceNotFoundException'
            )
        )
        return self.build_response(
            404,
            None,
            'ResourceNotFoundException'
        )

    def invalid_parameter_exception_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidParameterException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidParameterException'
        )

    def too_many_requests_exception_response(self) -> dict:
        logger.error(
            Exception(
                'TooManyRequestsException'
            )
        )
        return self.build_response(
            400,
            None,
            'TooManyRequestsException'
        )

    def unexpected_lambda_exception_response(self) -> dict:
        logger.error(
            Exception(
                'UnexpectedLambdaException'
            )
        )
        return self.build_response(
            400,
            None,
            'UnexpectedLambdaException'
        )

    def invalid_user_pool_config_exception_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidUserPoolConfigurationException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidUserPoolConfigurationException'
        )

    def user_lambda_validation_exception_response(self) -> dict:
        logger.error(
            Exception(
                'UserLambdaValidationException'
            )
        )
        return self.build_response(
            400,
            None,
            'UserLambdaValidationException'
        )

    def invalid_lambda_response_exception_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidLambdaResponseException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidLambdaResponseException'
        )

    def password_reset_required_exception_response(self) -> dict:
        logger.error(
            Exception(
                'PasswordResetRequiredException'
            )
        )
        return self.build_response(
            400,
            None,
            'PasswordResetRequiredException'
        )

    def user_not_found_exception_response(self, key: str) -> dict:
        logger.error(
            Exception(
                f'UserNotFoundException: {key} is not found.'
            )
        )
        return self.build_response(
            404,
            None,
            f'UserNotFoundException: {key} is not found.'
        )

    def internal_error_exception_response(self) -> dict:
        logger.error(
            Exception(
                'InternalErrorException'
            )
        )
        return self.build_response(
            400,
            None,
            'InternalErrorException'
        )

    def invalid_sms_role_access_policy_excep_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidSmsRoleAccessPolicyException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidSmsRoleAccessPolicyException'
        )

    def invalid_sms_role_trust_relation_expt_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidSmsRoleTrustRelationshipException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidSmsRoleTrustRelationshipException'
        )

    def invalid_email_role_access_policy_expt_response(self) -> dict:
        logger.error(
            Exception(
                'InvalidEmailRoleAccessPolicyException'
            )
        )
        return self.build_response(
            400,
            None,
            'InvalidEmailRoleAccessPolicyException'
        )

    def too_many_failed_attempts_except_response(self) -> dict:
        logger.error(
            Exception(
                'TooManyFailedAttemptsException'
            )
        )
        return self.build_response(
            401,
            None,
            'TooManyFailedAttemptsException'
        )

    def expired_code_except_response(self) -> dict:
        logger.error(
            Exception(
                'ExpiredCodeException'
            )
        )
        return self.build_response(
            401,
            None,
            'ExpiredCodeException'
        )

    def alias_exists_except_response(self) -> dict:
        logger.error(
            Exception(
                'AliasExistsException'
            )
        )
        return self.build_response(
            401,
            None,
            'AliasExistsException'
        )

    def limit_exceeded_except_response(self) -> dict:
        logger.error(
            Exception(
                'LimitExceededException'
            )
        )
        return self.build_response(
            401,
            None,
            'LimitExceededException'
        )

    def confirm_signup_response(self) -> dict:
        logger.info('Successfully registered')
        return self.build_response(
            200,
            None,
            'Successfully registered'
        )

    def fb_exception_response(self, e: Any) -> dict:
        logger.error(
            Exception(
                f'FacebookRequestError: {e.__str__()}'
            )
        )
        return self.build_response(
            400,
            None,
            f'FacebookRequestError: {e.__str__()}'
        )
