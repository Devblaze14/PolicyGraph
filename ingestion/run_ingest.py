import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from logging_utils import setup_logging, logger
from ingestion.seed_data import fetch_datasets
from ingestion.pipeline import IngestionPipeline
from retrieval.vector_store import FAISSVectorStore
from kg.graph_store import InMemoryGraphStore

def main() -> None:
    setup_logging()
    
    logger.info("Starting Data Ingestion Pipeline...")
    # Step 1: Ensure dataset exists
    config.paths.setup()
    if not list(config.paths.data_raw.glob("*.*")):
        logger.info("No raw data found. Fetching seed datasets from Indian Government Sources...")
        fetch_datasets()
        
    # Step 2: Initialize Stores
    logger.info("Initializing Graph and Vector Stores...")
    v_store = FAISSVectorStore()
    g_store = InMemoryGraphStore()
    
    # Optional Load
    v_store.load_index()
    g_store.load()

    # Step 3: Run pipeline
    pipeline = IngestionPipeline(vector_store=v_store, graph_store=g_store)
    logger.info(f"Ingesting directory: {config.paths.data_raw}")
    pipeline.ingest_directory(config.paths.data_raw)
    
    logger.info("Ingestion complete. Graph and Indexes saved to disk.")

if __name__ == "__main__":
    main()
