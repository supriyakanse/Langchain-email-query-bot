import os

from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Import configuration
from config import config


class SimpleConversationMemory:
    """Simple conversation memory for session-based chat history."""

    def __init__(self):
        self.chat_memory = InMemoryChatMessageHistory()
        self.memory_key = "chat_history"

    def save_context(self, inputs, outputs):
        """Save a conversation turn to memory."""
        if "input" in inputs:
            self.chat_memory.add_user_message(inputs["input"])
        if "output" in outputs:
            self.chat_memory.add_ai_message(outputs["output"])


def get_embeddings():
    """
    Initialize embeddings based on LLM_PROVIDER from config.

    Returns:
        Embeddings instance (OllamaEmbeddings or GoogleGenerativeAIEmbeddings)

    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    if config.LLM_PROVIDER == "ollama":
        return OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )
    elif config.LLM_PROVIDER == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=config.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}. Must be 'ollama' or 'gemini'"
        )


def get_llm():
    """
    Initialize LLM based on LLM_PROVIDER from config.

    Returns:
        LLM instance (ChatOllama or ChatGoogleGenerativeAI)

    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    if config.LLM_PROVIDER == "ollama":
        return ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            base_url=config.OLLAMA_BASE_URL,
        )
    elif config.LLM_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=config.LLM_TEMPERATURE,
            google_api_key=config.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}. Must be 'ollama' or 'gemini'"
        )


def load_vector_store(persist_directory=None):
    """
    Load the existing ChromaDB vector store from disk.

    Args:
        persist_directory: Directory where ChromaDB data is stored (uses config if not provided)

    Returns:
        Loaded Chroma vectorstore instance

    Raises:
        FileNotFoundError: If vector store doesn't exist
    """
    persist_dir = persist_directory or config.CHROMA_PERSIST_DIRECTORY

    # Check if vector store exists
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"Vector store not found at '{persist_dir}'. "
            "Please run the workflow to fetch and index emails first."
        )

    try:
        # Get embeddings based on provider
        embeddings = get_embeddings()

        vectorstore = Chroma(
            collection_name=config.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )
        return vectorstore
    except Exception as e:
        raise Exception(f"Failed to load vector store: {e}")


def query_emails(vectorstore, user_query, memory=None, k=None):
    """
    Query the email vector store and generate a natural language response.

    Args:
        vectorstore: ChromaDB vector store instance
        user_query: User's question about emails
        memory: Optional SimpleConversationMemory instance for conversational context
        k: Number of relevant emails to retrieve (uses config if not provided)

    Returns:
        Natural language response from the LLM

    Raises:
        Exception: If query processing fails
    """
    k = k or config.DEFAULT_RETRIEVAL_COUNT

    try:
        # Retrieve relevant emails using similarity search
        relevant_docs = vectorstore.similarity_search(user_query, k=k)

        # Format retrieved emails as context
        context = ""
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\n--- Email {i} ---\n"
            context += doc.page_content
            context += "\n"

        # Get LLM based on provider
        llm = get_llm()

        # Create prompt template with memory support
        if memory:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an intelligent email assistant. Answer the user's question based on the provided email context.
Be concise, accurate, and helpful. If the context doesn't contain enough information to answer the question, say so.
When counting or listing emails, be specific and accurate based on the provided context.
You can refer to previous conversation context when answering follow-up questions.""",
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    (
                        "user",
                        """Context (Retrieved Emails):
{context}

Question: {question}

Answer:""",
                    ),
                ]
            )
            # Build chain with memory
            chain = prompt | llm
            # Get conversation history from memory
            chat_history = memory.chat_memory.messages
            response = chain.invoke(
                {
                    "context": context,
                    "question": user_query,
                    "chat_history": chat_history,
                }
            )
            # Save conversation to memory
            memory.save_context({"input": user_query}, {"output": response.content})
        else:
            # No memory - simple prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an intelligent email assistant. Answer the user's question based on the provided email context.
Be concise, accurate, and helpful. If the context doesn't contain enough information to answer the question, say so.
When counting or listing emails, be specific and accurate based on the provided context.""",
                    ),
                    (
                        "user",
                        """Context (Retrieved Emails):
{context}

Question: {question}

Answer:""",
                    ),
                ]
            )
            chain = prompt | llm
            response = chain.invoke({"context": context, "question": user_query})

        return response.content

    except Exception as e:
        raise Exception(f"Failed to query emails: {e}")

