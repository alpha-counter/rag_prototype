import os
import shutil
import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LocalStorage:
    def __init__(self, source_directory):
        self.source_directory = source_directory
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        if not os.path.exists(self.source_directory):
            os.makedirs(self.source_directory)

    def load_documents(self):
        loader = PyPDFDirectoryLoader(self.source_directory, extract_images=False)
        documents = loader.load()

        if not documents:
            self.logger.error("No documents found in the source directory.")
            return []
        else:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=32, separators=["\n\n", "\n", " ", ""])
            docs = text_splitter.split_documents(documents)

            ## adding custom metadata
            # for i, chunks in enumerate(docs):
            #     docs[i].metadata['value'] = "test"

        return docs

    def _move_files(self, files):
        for file_name in files:
            source_file = os.path.join(self.source_directory, file_name)
            destination_file = os.path.join(self.processed_directory, file_name)
            shutil.move(source_file, destination_file)


# processor = LocalStorage('source_directory')
# documents = processor.load_documents()
