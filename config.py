import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model Configuration
GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/embedding-001"

# Text Processing Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Vector Store Configuration
COLLECTION_NAME = "saas_terms"
PERSIST_DIRECTORY = "vector_store" 