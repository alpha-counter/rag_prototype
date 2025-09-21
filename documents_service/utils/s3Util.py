import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import HTTPException
from typing import List
from fastapi import UploadFile
import os
from dotenv import load_dotenv

load_dotenv()

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION')
        )
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 25, # 25 MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25, # 25 MB
            use_threads=True
        )

    def upload_file(self, bucket_name, file_obj, file_name):
        try:
            self.s3_client.upload_fileobj(
                file_obj, 
                bucket_name, 
                file_name,
                Config=self.transfer_config
            )
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def download_file(self, bucket_name, file_name):
        try:
            file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=file_name)
            return file_obj['Body']
        except self.s3_client.exceptions.NoSuchKey:
            raise HTTPException(status_code=404, detail="File not found")
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def list_files(self, bucket_name):
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in response:
                files = [content['Key'] for content in response['Contents']]
                return files
            return []
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def list_files_in_folder(self, bucket_name, folder_name):
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name, Delimiter='/')
            if 'Contents' in response:
                files = [content['Key'] for content in response['Contents']]
                return files
            return []
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def delete_file(self, bucket_name, file_name):
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_name)
        except self.s3_client.exceptions.NoSuchKey:
            raise HTTPException(status_code=404, detail="File not found")
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def create_folder(self, bucket_name, folder_name):
        try:
            if not folder_name.endswith('/'):
                folder_name += '/'
            self.s3_client.put_object(Bucket=bucket_name, Key=folder_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def delete_folder(self, bucket_name, folder_name):
        try:
            if not folder_name.endswith('/'):
                folder_name += '/'
            objects_to_delete = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
            delete_keys = {'Objects': [{'Key': obj['Key']} for obj in objects_to_delete.get('Contents', [])]}
            if delete_keys['Objects']:
                self.s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def copy_file(self, source_bucket_name, source_file_name, dest_bucket_name, dest_file_name):
        try:
            copy_source = {'Bucket': source_bucket_name, 'Key': source_file_name}
            self.s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket_name, Key=dest_file_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def move_file(self, source_bucket_name, source_file_name, dest_bucket_name, dest_file_name):
        try:
            self.copy_file(source_bucket_name, source_file_name, dest_bucket_name, dest_file_name)
            self.delete_file(source_bucket_name, source_file_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def copy_folder(self, source_bucket_name, source_folder_name, dest_bucket_name, dest_folder_name):
        try:
            if not source_folder_name.endswith('/'):
                source_folder_name += '/'
            if not dest_folder_name.endswith('/'):
                dest_folder_name += '/'
            
            objects_to_copy = self.s3_client.list_objects_v2(Bucket=source_bucket_name, Prefix=source_folder_name)
            for obj in objects_to_copy.get('Contents', []):
                source_file_name = obj['Key']
                dest_file_name = source_file_name.replace(source_folder_name, dest_folder_name, 1)
                self.copy_file(source_bucket_name, source_file_name, dest_bucket_name, dest_file_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def move_folder(self, source_bucket_name, source_folder_name, dest_bucket_name, dest_folder_name):
        try:
            self.copy_folder(source_bucket_name, source_folder_name, dest_bucket_name, dest_folder_name)
            self.delete_folder(source_bucket_name, source_folder_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def generate_presigned_url(self, bucket_name, file_name, expiration=3600):
        try:
            url = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name, 'Key': file_name},
                                                        ExpiresIn=expiration)
            return url
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def make_file_public(self, bucket_name, file_name):
        try:
            self.s3_client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=file_name)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def make_folder_public(self, bucket_name, folder_name):
        try:
            if not folder_name.endswith('/'):
                folder_name += '/'
            objects_to_make_public = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
            for obj in objects_to_make_public.get('Contents', []):
                self.s3_client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=obj['Key'])
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="Credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=403, detail="Incomplete credentials")

    def upload_folder(self, bucket_name, files: List[UploadFile]):
        for file in files:
            self.upload_file(bucket_name, file.file, file.filename)
