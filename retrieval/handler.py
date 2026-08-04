from retrieval import embedder, retriever, generator
import json 

def handler(event, context = {}): 

    try:

        # Guard - if no query found
        if not event.get("query"):
            return {
                "statusCode" : 400, 
                "body" : json.dumps({
                    "message" : "No query provided to proceed further."
                })
            }

        # Step 1 - If query found, embed the query using the module
        embedded_user_query = embedder.embed_query(event.get("query"))

        # Step 2 - Pass the embedded user query to the Retriver module, which returns all the relevant chunks.
        relevant_chunks = retriever.retrieve_chunks(embedded_user_query)

        # Step 3 - Send the relevant chunks returned along with the the user query to the generator
        llm_response = generator.generate_answer(event.get("query"), relevant_chunks)
        
        return {
            "statusCode" : 200, 
            "body" : json.dumps({
                "answer" : llm_response,
                "chunks_used" : len(relevant_chunks)
            })
        }

    except Exception as e:
        return {
            "statusCode" : 500, 
            "body" : json.dumps({
                "message" : f"Unable to generate the response: {e}"
            })
        }