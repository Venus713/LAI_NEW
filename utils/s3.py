import os
from typing import Any
import boto3


class S3Client:
    region = os.environ['APP_REGION']
    s3bucket = os.environ['S3_BUCKET_NAME']

    def __init__(self):
        self.__s3_client = boto3.client(
            's3', region_name=self.region)

    def image_upload(self, pk: str, key: str, image: Any) -> str:
        """
        upload image to s3 bucket
        """
        self.__s3_client.put_object(
            Bucket=self.s3bucket, Key=f'{pk}/{key}', Body=image)
        photo_url = f'https://s3.{self.region}' + \
                    f'.amazonaws.com/{self.s3bucket}/{pk}/{key}'

        return photo_url
