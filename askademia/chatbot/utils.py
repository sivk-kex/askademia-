import os
import json
import numpy as np
from django.conf import settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from repo.models import Content, Folder

def get_llm_client():
    """Get the LLM client based on configuration"""
    llm_provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    
    if llm_provider == 'openai':
        os.environ["OPENAI_API_KEY"] = api_key
        return ChatOpenAI(
            temperature=0.2,
            model_name="gpt-3.5-turbo",
            max_tokens=500
        )
    elif llm_provider == 'gemini':
        # Implementation for Gemini API
        # This is a placeholder; actual implementation would depend on Gemini's API
        from langchain.llms import GooglePalm
        os.environ["GOOGLE_API_KEY"] = api_key
        return GooglePalm(temperature=0.2)
    elif llm_provider == 'llama':
        # Implementation for Llama API
        # This is a placeholder; actual implementation would depend on Llama's API format
        from langchain.llms import LlamaCpp
        return LlamaCpp(
            model_path="/path/to/llama/model.bin",
            temperature=0.2,
            max_tokens=500
        )
    else:
        # Default to OpenAI
        os.environ["OPENAI_API_KEY"] = api_key
        return ChatOpenAI(
            temperature=0.2,
            model_name="gpt-3.5-turbo",
            max_tokens=500
        )

def get_embeddings_model():
    """Get the embeddings model"""
    llm_provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    
    if llm_provider == 'openai':
        os.environ["OPENAI_API_KEY"] = api_key
        return OpenAIEmbeddings()
    else:
        # Default to OpenAI embeddings
        os.environ["OPENAI_API_KEY"] = api_key
        return OpenAIEmbeddings()

def create_vector_store(user):
    """Create or update vector store for user's content"""
    # Get all content for the user
    contents = Content.objects.filter(user=user)
    
    # Get all texts from content
    documents = []
    for content in contents:
        text = ""
        if content.content_type == 'text':
            # Read text file
            with open(content.file.path, 'r', encoding='utf-8') as file:
                text = file.read()
        elif content.content_type == 'pdf':
            # Use extracted text
            text = content.extracted_text
        elif content.content_type == 'link':
            # Use description as context
            text = f"Web Link: {content.web_link}\n{content.description}"
        else:
            # For images and videos, use the description
            text = content.description
        
        if text:
            documents.append({
                "page_content": text,
                "metadata": {
                    "id": content.id,
                    "title": content.title,
                    "type": content.content_type,
                    "folder": content.folder.name if content.folder else "Uncategorized"
                }
            })
    
    if not documents:
        return None
    
    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    # Split documents
    texts = []
    metadatas = []
    for doc in documents:
        chunks = text_splitter.split_text(doc["page_content"])
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append(doc["metadata"])
    
    # Create embeddings
    embeddings = get_embeddings_model()
    
    # Create vector store
    vector_store = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
    
    # Save vector store
    vector_store_path = os.path.join(settings.MEDIA_ROOT, 'vectorstores', f"user_{user.id}")
    os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
    vector_store.save_local(vector_store_path)
    
    return vector_store

def get_vector_store(user):
    """Get vector store for user"""
    vector_store_path = os.path.join(settings.MEDIA_ROOT, 'vectorstores', f"user_{user.id}")
    
    # Check if vector store exists
    if not os.path.exists(vector_store_path):
        return create_vector_store(user)
    
    # Load vector store
    embeddings = get_embeddings_model()
    try:
        vector_store = FAISS.load_local(vector_store_path, embeddings)
        return vector_store
    except:
        return create_vector_store(user)

def generate_response(user, query):
    """Generate response using RAG architecture"""
    # Get vector store
    vector_store = get_vector_store(user)
    
    if not vector_store:
        return "I don't have any knowledge to answer your question yet. Please add some content to your repository.", 0.0
    
    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    # Get relevant documents
    docs = retriever.get_relevant_documents(query)
    
    if not docs:
        return "I couldn't find relevant information in my knowledge base to answer your question.", 0.2
    
    # Calculate confidence score based on similarity
    confidence_score = calculate_confidence_score(docs, query)
    
    # Create prompt template
    prompt_template = """
    You are an AI assistant for an educational institution. Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say "I don't know" or "I don't have enough information about that", don't try to make up an answer.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create chain
    chain_type_kwargs = {"prompt": prompt}
    llm = get_llm_client()
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs=chain_type_kwargs,
        return_source_documents=False
    )
    
    # Generate response
    response = qa_chain({"query": query})
    
    return response["result"], confidence_score

def calculate_confidence_score(docs, query):
    """Calculate confidence score based on semantic similarity"""
    # This is a simple implementation; consider using cosine similarity with embeddings for more accuracy
    if not docs:
        return 0.0
    
    # Get embeddings for query and documents
    embeddings = get_embeddings_model()
    query_embedding = embeddings.embed_query(query)
    
    # Calculate similarity scores
    scores = []
    for doc in docs:
        doc_embedding = embeddings.embed_query(doc.page_content)
        similarity = cosine_similarity(query_embedding, doc_embedding)
        scores.append(similarity)
    
    # Average the top 3 scores or all if less than 3
    top_scores = sorted(scores, reverse=True)[:min(3, len(scores))]
    avg_score = sum(top_scores) / len(top_scores)
    
    return avg_score

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))