import os
import boto3
from typing import Any, List
from boto3.dynamodb.conditions import Attr, Key, And


class DynamoDb:
    table_name = os.environ['DB_TABLE_NAME']

    def __init__(self):
        if not self.table_name:
            raise ValueError('table_name property can not be empty.')

        dynamo_db = boto3.resource(
            'dynamodb', region_name=os.environ['APP_REGION'])
        self.__table = dynamo_db.Table(self.table_name)

    def create_item(self, pk: str, sk: Any, item: dict):
        """
        save new item into dynamodb table
        """
        item.update({
            'pk': pk,
            'sk': sk
        })
        return self.__table.put_item(Item=item)

    def filter_by_attr(self, data: dict = {}) -> List[dict]:
        """
        query an item from dynamodb table
        """
        if data:
            resp = self.__table.scan(
                FilterExpression=And(
                    *[(Attr(key).eq(value)) for key, value in data.items()])
            )
        else:
            resp = self.__table.scan()
        return resp['Items']

    def get_item(self, pk: str, sk: Any) -> dict:
        item = self.__table.get_item(Key={'pk': pk, 'sk': sk})
        return item.get('Item', {})

    def query_item(self, pk: str, data: dict) -> dict:
        for key, val in data.items():
            if key and val:
                item = self.__table.query(
                    KeyConditionExpression=Key('pk').eq(pk),
                    FilterExpression=Attr(key).eq(val)
                )
            else:
                params = {'KeyConditionExpression': Key('pk').eq(pk)}

                def __get_response() -> List[dict]:
                    response = self.__table.query(**params)
                    params['ExclusiveStartKey'] = response.get(
                                                    'LastEvaluatedKey')

                    return response.get('Items')

                item = __get_response()
                while params.get('ExclusiveStartKey'):
                    item += __get_response()

        print(f'{item=}')
        if type(item) is list:
            return item
        else:
            return item.get('Items')

    def update_item(self, pk: str, sk: Any, data: dict):
        """
        update an item
        """
        if not data:
            raise Exception('update parameter can not be empty.')

        update_expressions = []
        expression_attr_values = {}
        expression_attr_name = {}
        for attr, value in data.items():
            update_expressions.append(f'#{attr} = :{attr}_val')
            expression_attr_values[f':{attr}_val'] = value
            expression_attr_name[f'#{attr}'] = attr

        return self.__table.update_item(
            Key={
                'pk': pk,
                'sk': sk
            },
            UpdateExpression=f"SET {', '.join(update_expressions)}",
            ExpressionAttributeValues=expression_attr_values,
            ExpressionAttributeNames=expression_attr_name
        )

    def delete_item(
        self, pk: str, sk: Any, attr: str = None, value: Any = None
    ):
        """
        delete an item
        """
        if attr is None and value is None:
            return self.__table.update_item(
                Key={
                    'pk': pk,
                    'sk': sk
                }
            )
        else:
            return self.__table.update_item(
                Key={
                    'pk': pk,
                    'sk': sk
                },
                ConditionExpression=f'SET {attr} = :val',
                ExpressionAttributeValues={
                    ':val': value
                }
            )
