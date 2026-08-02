# Loading Voyage API key 
from shared.config import VOYAGE_API_KEY 
from langchain_voyageai import VoyageAIEmbeddings

# Created an object to do the embedding
embedder = VoyageAIEmbeddings(
    voyage_api_key = VOYAGE_API_KEY, 
    model = "voyage-3-lite"
)

def embed_chunks(chunks):

    # Creating a temporary list to only fetch the chunks from the input chunks list to pass it in one batch to the Voyage API 
    only_chunks_list = [chunk_data.get("chunk_text") for chunk_data in chunks]
    
    # Passing all chunks in one-go as Voyage AI supports batching
    vector_embeddings_for_all_chunks = embedder.embed_documents(only_chunks_list) 
    # Fall back for only one time embedding -- embedder.embed_query(text)

    # Combining the returned vectors back to the main input list hence enriching the same. 
    for chunk, vector_embedding in zip(chunks, vector_embeddings_for_all_chunks):
        # Creating a new key for each chunk from the chunks list
        chunk["embedding"] = vector_embedding

    return chunks # returning the enriched list 
