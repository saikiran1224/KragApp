from langchain_voyageai import VoyageAIEmbeddings 

from shared.config import VOYAGE_API_KEY

def embed_query(query):

    embedder = VoyageAIEmbeddings(
        voyage_api_key = VOYAGE_API_KEY, 
        model = "voyage-3-lite"
    )

    embedded_user_query = embedder.embed_query(query)

    return embedded_user_query