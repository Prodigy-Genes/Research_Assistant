import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIR = "./chroma_db"
    MAX_SEARCH_RESULTS = 5
    MAX_RAG_DOCS = 3