import json
import os
import logging
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import helpers
import sys

__path__ = sys.path[0]

class Config:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
        self.loader = DirectoryLoader('./captions', glob="**/*.cleaned.vtt", loader_cls=TextLoader, show_progress=True)
        self.subset_only = False
        self.loaded_file = 'loaded.json'
        self.captions_dir = './captions'
        self.db_persist_directory = 'db'
        self.log_file = 'document_processing.log'
        self.log_level = logging.DEBUG

def setup_logger(config: Config) -> logging.Logger:
    logger = logging.getLogger('DocumentProcessor')
    logger.setLevel(config.log_level)
    
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(config.log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.log_level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class FileProcessor:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.loaded = self._load_processed_files()

    def _load_processed_files(self) -> List[str]:
        if os.path.exists(self.config.loaded_file):
            self.logger.info(f"Loading processed files from {self.config.loaded_file}")
            return json.load(open(self.config.loaded_file))
        self.logger.info(f"No existing processed files found at {self.config.loaded_file}")
        return []

    def get_files_to_process(self) -> List[str]:
        all_files = [f for f in os.listdir(self.config.captions_dir) 
                     if 'cleaned' in f and f not in self.loaded 
                     and (not self.config.subset_only or f.startswith('_'))]
        self.logger.info(f"Found {len(all_files)} files to process")
        return sorted(all_files)

    def update_processed_files(self, processed_files: List[str]):
        self.loaded.extend(processed_files)
        with open(self.config.loaded_file, 'w') as f:
            json.dump(self.loaded, f)
        self.logger.info(f"Updated processed files list with {len(processed_files)} new files")

class DocumentProcessor:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def process_documents(self) -> List[Dict]:
        self.logger.info("Starting document processing")
        docs = self.config.loader.load()
        self.logger.info(f"Loaded {len(docs)} documents")
        splits = self.config.splitter.split_documents(docs)
        self.logger.info(f"Created {len(splits)} splits from the documents")
        return splits

    def enrich_metadata(self, all_splits: List[Dict], files_to_process: List[str]):
        self.logger.info(f"Enriching metadata for {len(files_to_process)} files")
        enriched_count = 0
        for filename in files_to_process:
            video_id = filename.split('.')[0]
            metadata = self._get_metadata(video_id)
            
            for document in all_splits:
                if document.metadata['source'].split('/')[-1] == filename:
                    document.metadata = metadata
                    enriched_count += 1
        
        self.logger.info(f"Enriched metadata for {enriched_count} splits across all files")
        return all_splits

    def _get_metadata(self, video_id: str) -> Dict:
        metadata = {
            'title': 'Unknown',
            'description': 'Unknown',
            'url': helpers.get_video_url(video_id),
            'source': video_id,
        }
        video = helpers.get_video_info(video_id)
        if video is not None:
            metadata['title'] = video['snippet']['title']
            metadata['description'] = video['snippet']['description']
            self.logger.debug(f"Retrieved metadata for video {video_id}: {metadata['title']}")
        else:
            self.logger.warning(f"Could not retrieve metadata for video {video_id}")
        return metadata

class ChromaDBHandler:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def store_documents(self, documents: List[Dict]):
        self.logger.info(f"Storing {len(documents)} documents in ChromaDB")
        try:
            Chroma.from_documents(documents, self.config.embedding_model, persist_directory=self.config.db_persist_directory)
            self.logger.info("Successfully stored documents in ChromaDB")
        except Exception as e:
            self.logger.error(f"Error storing documents in ChromaDB: {str(e)}")
            raise

def main():
    config = Config()
    logger = setup_logger(config)
    logger.info("Starting document processing script")

    file_processor = FileProcessor(config, logger)
    document_processor = DocumentProcessor(config, logger)
    db_handler = ChromaDBHandler(config, logger)

    try:
        files_to_process = file_processor.get_files_to_process()
        all_splits = document_processor.process_documents()
        
        enriched_splits = document_processor.enrich_metadata(all_splits, files_to_process)
        db_handler.store_documents(enriched_splits)

        file_processor.update_processed_files(files_to_process)
        logger.info("Document processing completed successfully")
    except Exception as e:
        logger.error(f"An error occurred during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()