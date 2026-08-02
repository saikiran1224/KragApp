from ingestion import loader, chunker, embedder, store 
import json 

def handler(event, context = {}):

    try: 
        # No file upload - returning 400 
        if not event.get("file_path"):
            return {
                "statusCode" : 400, 
                "body" : json.dumps({
                    "message" : "No file detected. Please upload the file and try again."
                })
            }

        file_path = event.get("file_path") 

        # Step 1 - Load the file_path, determine file type, and return the raw python string parsed from document 
        document_info_containing_parsed_text = loader.load_document(file_path=file_path)

        # Step 2 - Pass the raw text data to the chunker which returns the chunks list 
        chunks_list = chunker.chunk_document(text=document_info_containing_parsed_text.get("text"))

        # Step 3 - Using the output of chunks_list (text form) convert into embeddings using embedder
        enriched_chunks_list_with_embeddings = embedder.embed_chunks(chunks=chunks_list)

        # Step 4 - Pass the document_text and enriched_chunks list to insert the doc and chunks into the Vector database
        document_id = store.store_document(
            document_info=document_info_containing_parsed_text,
            chunks=enriched_chunks_list_with_embeddings
        )

        # Step 5 - Once everything went successful, sending a 200 OK 
        return {
            "statusCode" : 200, 
            "body" : json.dumps({
                "message" : "Document ingestion successful.",
                "document_id" : document_id,
                "chunks_stored" : len(enriched_chunks_list_with_embeddings)
            })
        }

    except Exception as e:
        return {
            "statusCode" : 500, 
            "body" : json.dumps({
                "message" : f"Some Error occurred during Ingestion: {e}"
            })
        }
