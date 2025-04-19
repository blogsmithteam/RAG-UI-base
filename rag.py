import os
import logging
from openai import OpenAI
from pinecone import Pinecone

# Configure logging
logger = logging.getLogger(__name__)

# Load API keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "blogsmith-index")

# Check if API keys are available
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
if not PINECONE_API_KEY:
    logger.warning("Pinecone API key not found. Please set the PINECONE_API_KEY environment variable.")

# Initialize clients
try:
    # OpenAI client for embeddings and completions
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Pinecone client for vector database operations
    pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get the Pinecone index
    index = pinecone_client.Index(INDEX_NAME)
    
    logger.info(f"Successfully connected to Pinecone index: {INDEX_NAME}")
except Exception as e:
    logger.exception("Failed to initialize clients")
    raise RuntimeError(f"Failed to initialize clients: {str(e)}")

def get_embedding(text):
    """
    Generate an embedding for the given text using OpenAI's embedding model.
    
    Args:
        text (str): The text to convert to an embedding
        
    Returns:
        list: The embedding vector
    """
    try:
        logger.debug(f"Generating embedding for text: {text[:50]}...")
        response = openai_client.embeddings.create(
            input=[text], 
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.exception("Error generating embedding")
        raise Exception(f"Failed to generate embedding: {str(e)}")

def retrieve_context(query_text, top_k=5):
    """
    Retrieve relevant context from Pinecone based on query embedding.
    
    Args:
        query_text (str): The query text
        top_k (int): Number of top results to retrieve
        
    Returns:
        tuple: (list of context chunks, set of source URLs)
    """
    try:
        # Generate embedding for the query
        embedding = get_embedding(query_text)
        
        # Query Pinecone index
        logger.debug(f"Querying Pinecone index with top_k={top_k}")
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Extract text and sources from results
        context_chunks = []
        sources = set()
        
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            text = metadata.get("text", "")
            url = metadata.get("url", "")
            
            if text:
                context_chunks.append(f"{text}\n\nSource: {url}")
                if url:
                    sources.add(url)
        
        logger.info(f"Retrieved {len(context_chunks)} context chunks from {len(sources)} sources")
        return context_chunks, sources
    
    except Exception as e:
        logger.exception("Error retrieving context")
        raise Exception(f"Failed to retrieve context: {str(e)}")

def generate_answer(query_text, context_chunks, custom_api_key=None):
    """
    Generate an answer using OpenAI based on the query and retrieved context.
    
    Args:
        query_text (str): The query text
        context_chunks (list): List of relevant context chunks
        custom_api_key (str, optional): Custom OpenAI API key to use instead of the default
        
    Returns:
        str: The generated answer
    """
    try:
        # Join context chunks with separators
        context = "\n\n---\n\n".join(context_chunks)
        
        # Construct the prompt
        prompt = f"""You are a helpful assistant answering questions based on blog content.

Answer the following question using ONLY the information below. Cite the sources when relevant. If the answer isn't available, say you don't know.

QUESTION:
{query_text}

CONTEXT:
{context}

ANSWER:"""

        # Create a temporary client with the custom API key if provided
        client = openai_client
        if custom_api_key:
            logger.debug("Using custom OpenAI API key")
            client = OpenAI(api_key=custom_api_key)
        
        # Generate completion
        logger.debug("Generating answer with OpenAI")
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # Extract and return the answer
        answer = completion.choices[0].message.content.strip()
        logger.info(f"Generated answer of length {len(answer)}")
        return answer
    
    except Exception as e:
        logger.exception("Error generating answer")
        raise Exception(f"Failed to generate answer: {str(e)}")

def retrieve_and_generate_answer(query_text, top_k=5, custom_api_key=None):
    """
    Main function that combines retrieval and generation for RAG.
    
    Args:
        query_text (str): The query text
        top_k (int): Number of top results to retrieve
        custom_api_key (str, required): The user's OpenAI API key
        
    Returns:
        tuple: (answer, set of source URLs)
    """
    # Validate API key is provided
    if not custom_api_key:
        raise ValueError("OpenAI API key is required")
        
    # Retrieve relevant context
    context_chunks, sources = retrieve_context(query_text, top_k)
    
    # If no context found, return a message
    if not context_chunks:
        return "I don't have enough information to answer this question based on the available content.", []
    
    # Generate an answer based on the retrieved context
    answer = generate_answer(query_text, context_chunks, custom_api_key)
    
    return answer, sources
