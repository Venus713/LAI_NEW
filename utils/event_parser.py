import json
from .logging import logger
from .response import Response

response: Response = Response()


class EventParser:
    def filed_validation(self, data: dict, keys: tuple):
        for key in keys:
            if data.get(key) is None:
                return response.not_found_param_response(key), False
        return data, True

    def get_params(
        self, lambda_name: str, key: str, event: dict, fields: tuple
    ):
        if key == 'body':
            params = json.loads(event[key])
        else:
            params = event[key]
        logger.info(f'Request {key} in {lambda_name}: {params}')

        resp, res = self.filed_validation(params, fields)
        if res:
            return params, True
        else:
            return resp, res
