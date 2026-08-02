import psycopg2 # Postgres DB connection library (also being used by LangChain)
from psycopg2.extras import execute_values

from shared.config import DATABASE_URL
import json

def store_document(document_info, chunks): 
    """
     document_info - dict from loader.py — has file_name, file_type, metadata
     chunks - enriched list from embedder.py — has chunk_text, chunk_index, embedding
    """
    conn = None 
    
    try: 

        # Step 0 - Connecting to the PostgreSQL Database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor() # created one cursor obj to perform all DB operations. 

        # Step 1 - Create a row inside the documents table with the data from the document_info dict - Simple insert operation - One transaction 
        cursor.execute(""" 
            INSERT INTO documents (file_name, file_type, metadata) 
            VALUES (%s, %s, %s)
            RETURNING document_id
        """, (
                document_info.get("file_name"),
                document_info.get("file_type"),
                json.dumps(document_info.get("metadata", {}))
            )
        )

        # Step 2 - Fetch the returned document_id value from Step 1 and store it in a variable, as we need this as Foreign key to load all our chunks 
        document_id = cursor.fetchone()[0]

        # Step 3 - Insert all the chunks into the chunks table using the document_id as the foreign key. 
        # Note: Usually if our document is having 100+ chunks, we need to have 100 transactions which is cost and time-effective, hence psycopg2 lib supports bulk insert using `execute_values`
        execute_values(cursor, """ 
            INSERT INTO chunks (document_id, chunk_text, embedding, chunk_index, metadata)
            VALUES %s
            """, 
            [
                (document_id, chunk.get("chunk_text"), json.dumps(chunk.get("embedding")), chunk.get("chunk_index"), json.dumps({})) # Should be in TUPLE format to be accepted by %s 
                for chunk in chunks
            ] # List Comprehension
        )

        # Step 4 - Commiting and closing the cursor object
        conn.commit()

        # Step 5 - Returning the document_id 
        return document_id

    except Exception as e: 
        # Rolling back the above transactions to avoid half-cooked entries in the Database
        if conn:
            conn.rollback()
        raise
    
    finally:
        if conn:
            # Closing the cursor object and the connection
            cursor.close()
            conn.close()


