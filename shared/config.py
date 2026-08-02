# This is a helper file - usage is to set all the shared variables like DB_INSTANCE_URL, etc. 

from dotenv import load_dotenv
load_dotenv() # Injecting the .env file into the Host OS Environment variable

import os 

try: 
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]
    VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
    POSTGRESQL_DB_PASSWORD = os.environ["POSTGRESQL_DB_PASSWORD"]
except KeyError: 
    raise KeyError()

DATABASE_URL = f"postgresql://kragapp_admin:{POSTGRESQL_DB_PASSWORD}@localhost:5432/kragapp_db"
GROQ_MODEL = "llama-3.1-8b-instant"
CHUNK_SIZE = 512 # Max No. of characters in one chunk 
CHUNK_OVERLAP = 50 # Notation in Characters
EMBEDDING_DIM = 512 # Voyage-3-lite embedding model output is 512 dimensions 
