import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
INDEX_NAME = os.environ["INDEX_NAME"]

DATA_DIR = Path(__file__).parent / "data"
NAMESPACE = "fastapi-docs"

EMBEDDING_MODEL = "text-embedding-3-small"
DIMENSION = 1536

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80
TOP_K = 5
