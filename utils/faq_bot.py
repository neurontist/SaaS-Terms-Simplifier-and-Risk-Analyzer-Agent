from typing import List, Dict, Any
import chromadb
from langchain.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from config import GOOGLE_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL

class FAQBot:
    def __init__(self, api_key: str = None):
        """
        Initialize the FAQ chatbot with Gemini API and ChromaDB.
        
        Args:
            api_key (str): Google Gemini API key
        """
        self.api_key = api_key or GOOGLE_API_KEY
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=self.api_key
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        try:
            # Try to get existing collection
            self.collection = self.chroma_client.get_collection("saas_terms")
        except ValueError:
            # Create new collection if it doesn't exist
            self.collection = self.chroma_client.create_collection("saas_terms")
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Initialize prompt template
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""
            You are a helpful assistant answering questions about SaaS Terms & Conditions.
            Use the following context to answer the question. If you don't know the answer,
            say that you don't know. Don't make up answers.
            
            Context: {context}
            
            Chat History: {chat_history}
            
            Question: {question}
            
            Answer:
            """
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents with metadata
        """
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        ids = [str(i) for i in range(len(documents))]
        
        # Create vector store
        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            ids=ids,
            collection_name="saas_terms"
        )
        
        # Initialize conversation chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt}
        )
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Ask a question about the terms.
        
        Args:
            question (str): User's question
            
        Returns:
            Dict[str, Any]: Answer with metadata
        """
        if not hasattr(self, 'qa_chain'):
            return {
                "answer": "Please add documents first before asking questions.",
                "metadata": {"error": "No documents loaded"}
            }
        
        try:
            # Get answer from the chain
            result = self.qa_chain({"question": question})
            
            return {
                "answer": result["answer"],
                "metadata": {
                    "question": question,
                    "sources": result.get("source_documents", [])
                }
            }
        except Exception as e:
            return {
                "answer": f"Error getting answer: {str(e)}",
                "metadata": {"error": str(e)}
            }
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self.memory.clear() 