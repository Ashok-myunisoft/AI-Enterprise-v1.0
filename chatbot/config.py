import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL             = os.getenv("DATABASE_URL")
CHATBOT_PORT             = int(os.getenv("CHATBOT_PORT", "8010"))
FAISS_INDEX_PATH         = os.getenv("FAISS_INDEX_PATH", "./faiss_indexes")
EMBEDDING_MODEL          = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
HISTORY_LIMIT            = int(os.getenv("HISTORY_LIMIT", "20"))
CHATBOT_INTERNAL_SECRET  = os.getenv("CHATBOT_INTERNAL_SECRET")
