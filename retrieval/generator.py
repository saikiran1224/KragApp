from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from shared.config import GROQ_API_KEY, GROQ_MODEL

def generate_answer(query, chunks): 
    
    if len(chunks) == 0: 
        return "No Relevant context is found for your query. Please try to rephrase your prompt and try again."

    # Initializing the Groq LLM
    llm = ChatGroq(
        api_key = GROQ_API_KEY,
        model_name = GROQ_MODEL
    )

    # Extracting all the chunk_test and combining into one 
    complete_chunk_text = "\n---\n".join([chunk["chunk_text"] for chunk in chunks])

    # Building the System Message 
    system_message = SystemMessage(
        content=""" 
        You are a helpful assistant. Answer the question using ONLY
        the context provided below. If the answer is not in the context,
        say you don't know.
        """
    )

    # Building the Human Message - top_k chunks attached with user prompt
    human_message = HumanMessage(
        content=f""" 
        
        Context: {complete_chunk_text}

        Question: {query}

        Answer:
        
        """
    )

    # Invoking the LLM with the below messages
    messages = [system_message, human_message]
    
    # Capturing the response upon invocation
    response = llm.invoke(messages)

    return response.content # Returning the content


