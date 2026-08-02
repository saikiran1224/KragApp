from langchain_text_splitters import RecursiveCharacterTextSplitter
from shared.config import CHUNK_SIZE, CHUNK_OVERLAP

# Function which takes the raw string and returns back the chunks in form of a dictionary
def chunk_document(text): 

    if (not text) or (not text.strip()):
        raise ValueError("Empty text cannot be chunked.")

    # Creating the text splitter
    recursive_char_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE, # In characters
        chunk_overlap = CHUNK_OVERLAP # In characters
    ) 

    chunks_list = recursive_char_text_splitter.split_text(text)

    formatted_chunk_with_index_list = []

    for chunk_index, chunk_text in enumerate(chunks_list):

        formatted_chunk_with_index_list.append({
            "chunk_text" : chunk_text,
            "chunk_index" : chunk_index
        })

    return formatted_chunk_with_index_list
