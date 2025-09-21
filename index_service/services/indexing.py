import os
import re
import logging
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import S3FileLoader
from langchain.schema import Document
from langchain.indexes import SQLRecordManager, index
from langchain_postgres import PGVector
from index_service.utils.storageLocalUtil import LocalStorage
from index_service.utils.storageS3Util import S3Storage
from index_service.utils.dbUtil import create_database_if_not_exists

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class IndexService:
    def __init__(self):
        self.S3_SOURCE_BUCKET = os.getenv("S3_SOURCE_BUCKET")
        self.S3_PROCESSED_BUCKET = os.getenv("S3_PROCESSED_BUCKET")
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
        
        self.DOMAIN = os.getenv("DOMAIN")
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.VECTORDB_URL = os.getenv("VECTORDB_URL")

        # Get the string segment after the final '/'
        match = re.search(r'[^/]+$', self.VECTORDB_URL) 
        self.VECTORDB_NAME = match.group(0)

        # Create the Vector Database
        create_database_if_not_exists(self.DATABASE_URL, self.VECTORDB_NAME )
        
        # Initialize record manager
        namespace = f"{self.DOMAIN}/{self.VECTORDB_NAME}"
        self.record_manager = SQLRecordManager(namespace=namespace, db_url=self.VECTORDB_URL)
        self.record_manager.create_schema()
        
        # Initialize embeddings and vectorstore
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = PGVector(
            self.embeddings,
            collection_name=self.VECTORDB_NAME,
            connection=self.VECTORDB_URL
        )

    def all(self, source: str, storage_type: str):    
        match storage_type:
            case 'local':
                DocumentProcessor = LocalStorage(source)
            case 's3':
                DocumentProcessor = S3Storage(
                    source,
                    self.AWS_ACCESS_KEY_ID, 
                    self.AWS_SECRET_ACCESS_KEY, 
                    self.AWS_DEFAULT_REGION, 
                    batch_size=100, 
                    max_workers=10
                )
            case _:
                raise ValueError(f"Unsupported storage type: {storage_type}")

        docs = DocumentProcessor.load_documents()
        result = self.upsert_index(docs)
        return result

    def upsert_index(self, docs: list):
        if not docs:
            logger.error("No documents found.")
            return None

        logger.info(f"Loaded {len(docs)} documents.")

        # Index documents
        result = index(
            docs,
            self.record_manager,
            self.vectorstore,
            cleanup="full",
            source_id_key="source",
        )

        logger.info(result)
        return result

# index = IndexService()
# result = index.all("/path/to/source", "local")
