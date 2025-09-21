import os
import shutil
import boto3
import logging
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError, ClientError
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


class S3Storage:
    def __init__(self, source_bucket, aws_access_key_id=None, aws_secret_access_key=None, region_name=None, batch_size=100, max_workers=10):
        self.source_bucket = source_bucket
        self.s3 = boto3.client('s3', 
                               aws_access_key_id=aws_access_key_id, 
                               aws_secret_access_key=aws_secret_access_key, 
                               region_name=region_name)
        self.batch_size = batch_size
        self.max_workers = max_workers
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_documents(self):
        try:
            files = []
            continuation_token = None

            # Paginate through all objects in the source bucket
            while True:
                if continuation_token:
                    response = self.s3.list_objects_v2(Bucket=self.source_bucket, ContinuationToken=continuation_token)
                else:
                    response = self.s3.list_objects_v2(Bucket=self.source_bucket)

                if 'Contents' in response:
                    files.extend([obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.pdf')])

                if 'NextContinuationToken' in response:
                    continuation_token = response['NextContinuationToken']
                else:
                    break

            if not files:
                self.logger.error("No PDF files found in the source bucket.")
                return []

            # Process files in batches
            documents = []
            for i in range(0, len(files), self.batch_size):
                batch_files = files[i:i+self.batch_size]
                documents.extend(self._process_batch(batch_files))

            return documents

        except NoCredentialsError:
            self.logger.error("Credentials not available.")
            return []
        except ClientError as e:
            self.logger.error(f"Client error: {e}")
            return []

    def _process_batch(self, batch_files):
        temp_directory = '/tmp/s3_temp'
        os.makedirs(temp_directory, exist_ok=True)
        local_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for file_key in batch_files:
                local_path = os.path.join(temp_directory, file_key)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                executor.submit(self._download_file, file_key, local_path)
                local_files.append(local_path)

        loader = PyPDFDirectoryLoader(temp_directory, extract_images=False)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=32, separators=["\n\n", "\n", " ", ""])
        docs = text_splitter.split_documents(documents)
        
        ## adding custom metadata
        # for i, chunks in enumerate(docs):
        #     docs[i].metadata['value'] = "test"

        shutil.rmtree(temp_directory)
        return docs

    def _download_file(self, file_key, local_path):
        try:
            self.s3.download_file(self.source_bucket, file_key, local_path)
        except ClientError as e:
            self.logger.error(f"Error downloading {file_key}: {e}")


# processor = S3Storage('source-bucket-name', 'aws-access-key-id', 'aws-secret-access-key', 'region-name', batch_size=100, max_workers=10)
# documents = processor.load_documents()