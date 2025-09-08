import boto3, os
from botocore.exceptions import BotoCoreError, ClientError
from config import settings

class S3Service:
    def __init__(self):
        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket = settings.s3_bucket_name
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 client: {e}")

    def list_objects(self, prefix=None):
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix or "")
            contents = response.get('Contents', [])
            return [obj['Key'] for obj in contents]
        except ClientError as e:
            raise RuntimeError(f"AWS ClientError: {e}")
        except BotoCoreError as e:
            raise RuntimeError(f"AWS BotoCoreError: {e}")
        except Exception as e:
            raise RuntimeError(f"Error listing S3 objects: {e}")

    def download_object(self, key, dest_path):
        try:
            self.s3.download_file(self.bucket, key, dest_path)
            return True
        except ClientError as e:
            raise RuntimeError(f"AWS ClientError: {e}")
        except BotoCoreError as e:
            raise RuntimeError(f"AWS BotoCoreError: {e}")
        except Exception as e:
            raise RuntimeError(f"Error downloading S3 object '{key}': {e}")

    def download_folder(self, folder_prefix, dest_dir):
        try:
            objects = self.list_objects(prefix=folder_prefix)
            for key in objects:
                rel_path = key[len(folder_prefix):].lstrip('/')
                local_path = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                self.download_object(key, local_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Error downloading S3 folder '{folder_prefix}': {e}")
