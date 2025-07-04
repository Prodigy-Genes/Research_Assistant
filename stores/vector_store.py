import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    """ChromaDB-based vector store for RAG"""
    
    def __init__(self, collection_name: str = "research_docs"):
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
        
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Research documents collection"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store"""
        try:
            texts = [doc["content"] for doc in documents]
            embeddings = self.embedding_model.encode(texts).tolist()
            
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=[doc.get("metadata", {}) for doc in documents],
                ids=[f"doc_{i}_{datetime.now().timestamp()}" for i in range(len(documents))]
            )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
    
    def similarity_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=k
            )
            
            docs = []
            for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                docs.append({
                    "content": doc,
                    "metadata": metadata,
                    "source": metadata.get("source", "unknown"),
                    "score": results["distances"][0][i] if results["distances"] else 0
                })
            
            return docs
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []