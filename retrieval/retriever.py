from shared.config import DATABASE_URL
from pgvector.psycopg2 import register_vector
import numpy as np
import psycopg2

def retrieve_chunks(query_vector, top_k = 5):
    
    conn = None 

    try: 

        conn = psycopg2.connect(DATABASE_URL) 
        register_vector(conn)  # ← tells psycopg2 how to handle vector type

        cursor = conn.cursor()

        # Performing the cosine similarity (<=>) check using the user provided vector with the available chunks inside the pgvector database
        cursor.execute(
            """ 
            SELECT chunk_text, chunk_index, document_id, embedding <=> %s AS distance
            FROM chunks
            ORDER BY embedding <=> %s 
            LIMIT %s
            """, (
                    np.array(query_vector), 
                    np.array(query_vector), 
                    top_k
            )
        )

        # Fetching all the returned chunks
        top_k_chunks = cursor.fetchall()

        # Creating a fresh list to store the formatted chunks in dict 
        formatted_chunks_list = []

        for chunk in top_k_chunks:
            formatted_chunks_list.append(
                {
                    "chunk_text" : chunk[0],
                    "chunk_index" : chunk[1],
                    "document_id" : chunk[2],
                    "distance" : chunk[3]
                }
            )

        return formatted_chunks_list

    except Exception as e: 

        # Rolling back the above transactions to avoid half-cooked entries in the Database
        if conn:
            conn.rollback()
        raise 

    finally:
        if conn: # if connection object present
            cursor.close()
            conn.close()
        
