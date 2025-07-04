import os
import json
import requests
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from pathlib import Path

# Third-party imports
from langgraph.graph import StateGraph, END
import openai
import chromadb
from sentence_transformers import SentenceTransformer
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-4" for better quality
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight embedding model
    CHROMA_PERSIST_DIR = "./chroma_db"
    MAX_SEARCH_RESULTS = 5
    MAX_RAG_DOCS = 3

# Initialize OpenAI client
openai.api_key = Config.OPENAI_API_KEY

# Initialize embedding model
embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)

# State definition
class ResearchState(TypedDict):
    question: str
    tool_choice: str
    search_results: List[Dict[str, Any]]
    rag_docs: List[Dict[str, Any]]
    answer: str
    citations: List[str]
    memory_context: List[Dict[str, Any]]
    error: Optional[str]

class ToolChoice(Enum):
    WEB_SEARCH = "web_search"
    PDF_SUMMARIZE = "pdf_summarize"
    MEMORY_LOOKUP = "memory_lookup"

class VectorStore:
    """ChromaDB-based vector store for RAG"""
    
    def __init__(self, collection_name: str = "research_docs"):
        self.collection_name = collection_name
        try:
            self.collection = chroma_client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            self.collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Research documents collection"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store"""
        try:
            texts = [doc["content"] for doc in documents]
            embeddings = embedding_model.encode(texts).tolist()
            
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
            query_embedding = embedding_model.encode([query]).tolist()
            
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

class MemoryStore:
    """Simple JSON-based memory store"""
    
    def __init__(self, file_path: str = "memory_store.json"):
        self.file_path = file_path
        self.memory = self._load_memory()
    
    def _load_memory(self) -> List[Dict[str, Any]]:
        """Load memory from file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
        return []
    
    def save_memory(self) -> None:
        """Save memory to file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def add_entry(self, question: str, answer: str, citations: List[str] = None) -> None:
        """Add a new Q&A entry"""
        entry = {
            "question": question,
            "answer": answer,
            "citations": citations or [],
            "timestamp": datetime.now().isoformat()
        }
        self.memory.append(entry)
        self.save_memory()
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory for relevant entries"""
        query_words = set(query.lower().split())
        scored_entries = []
        
        for entry in self.memory:
            question_words = set(entry["question"].lower().split())
            answer_words = set(entry["answer"].lower().split())
            
            # Simple word overlap scoring
            score = len(query_words & question_words) + 0.5 * len(query_words & answer_words)
            
            if score > 0:
                scored_entries.append((score, entry))
        
        # Sort by score and return top results
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

# Initialize global instances
vector_store = VectorStore()
memory_store = MemoryStore()

# API Integration Classes
class BraveSearchAPI:
    """Brave Search API integration"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    @staticmethod
    def search(query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Perform web search using Brave Search API"""
        if not Config.BRAVE_API_KEY:
            logger.error("Brave API key not configured")
            return []
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": Config.BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": count,
            "result_filter": "web",
            "safesearch": "moderate"
        }
        
        try:
            response = requests.get(BraveSearchAPI.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for result in data.get("web", {}).get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("description", ""),
                    "url": result.get("url", ""),
                    "published": result.get("age", ""),
                    "source": result.get("profile", {}).get("name", "web")
                })
            
            logger.info(f"Retrieved {len(results)} search results for: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error performing web search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in web search: {e}")
            return []

class OpenAIAPI:
    """OpenAI API integration"""
    
    @staticmethod
    def generate_response(prompt: str, max_tokens: int = 1000) -> str:
        """Generate response using OpenAI API"""
        if not Config.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            return "Error: OpenAI API key not configured"
        
        try:
            response = openai.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant. Provide accurate, well-cited responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return f"Error generating response: {str(e)}"

class PDFProcessor:
    """PDF processing utilities"""
    
    @staticmethod
    def extract_text_from_url(url: str) -> str:
        """Extract text from PDF URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Save temporarily
            temp_path = "temp_pdf.pdf"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Extract text
            text = PDFProcessor.extract_text_from_file(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF URL: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF file: {e}")
            return ""

# Graph node functions
def receive_question(state: ResearchState) -> Dict[str, Any]:
    """Entry node that processes the user's question"""
    question = state.get("question", "").strip()
    logger.info(f"📝 Received question: {question}")
    
    if not question:
        return {"error": "No question provided"}
    
    return {"question": question}

def select_tool(state: ResearchState) -> Dict[str, Any]:
    """Determine which tool to use based on the question"""
    question = state["question"].lower()
    
    if any(keyword in question for keyword in ["pdf", "document", "summarize", "file"]):
        tool_choice = ToolChoice.PDF_SUMMARIZE.value
    elif any(keyword in question for keyword in ["search", "web", "current", "news", "recent", "latest"]):
        tool_choice = ToolChoice.WEB_SEARCH.value
    else:
        tool_choice = ToolChoice.MEMORY_LOOKUP.value
    
    logger.info(f"🔧 Selected tool: {tool_choice}")
    return {"tool_choice": tool_choice}

def web_search(state: ResearchState) -> Dict[str, Any]:
    """Perform web search using Brave Search API"""
    question = state["question"]
    logger.info(f"🔍 Performing web search for: {question}")
    
    search_results = BraveSearchAPI.search(question, Config.MAX_SEARCH_RESULTS)
    
    if not search_results:
        return {"error": "No search results found"}
    
    # Add search results to vector store for future RAG
    documents = [
        {
            "content": f"{result['title']}\n{result['snippet']}",
            "metadata": {
                "source": result["url"],
                "title": result["title"],
                "type": "web_search"
            }
        }
        for result in search_results
    ]
    
    vector_store.add_documents(documents)
    
    return {"search_results": search_results}

def pdf_summarize(state: ResearchState) -> Dict[str, Any]:
    """Summarize PDF documents related to the question"""
    question = state["question"]
    logger.info(f"📄 Processing PDF for: {question}")
    
    # Extract URL from question (simple regex or manual parsing)
    # In production, you might want more sophisticated URL extraction
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', question)
    
    if not urls:
        return {"error": "No PDF URL found in question"}
    
    pdf_url = urls[0]
    text = PDFProcessor.extract_text_from_url(pdf_url)
    
    if not text:
        return {"error": "Could not extract text from PDF"}
    
    # Chunk the text for better processing
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    
    # Add to vector store
    documents = [
        {
            "content": chunk,
            "metadata": {
                "source": pdf_url,
                "type": "pdf",
                "chunk_id": i
            }
        }
        for i, chunk in enumerate(chunks)
    ]
    
    vector_store.add_documents(documents)
    
    # Generate summary using OpenAI
    summary_prompt = f"""
    Summarize the following PDF content in relation to the question: "{question}"
    
    PDF Content:
    {text[:3000]}...
    
    Please provide a concise summary highlighting the key points relevant to the question.
    """
    
    summary = OpenAIAPI.generate_response(summary_prompt)
    
    search_results = [
        {
            "title": f"PDF Summary: {question}",
            "snippet": summary,
            "url": pdf_url,
            "source": "PDF Document"
        }
    ]
    
    return {"search_results": search_results}

def memory_lookup(state: ResearchState) -> Dict[str, Any]:
    """Look up previous conversations from memory"""
    question = state["question"]
    logger.info(f"🧠 Looking up memory for: {question}")
    
    relevant_memory = memory_store.search_memory(question, limit=3)
    
    search_results = [
        {
            "title": f"Previous Q&A: {mem['question']}",
            "snippet": mem["answer"][:300] + "..." if len(mem["answer"]) > 300 else mem["answer"],
            "url": "memory",
            "source": "Previous Conversation",
            "timestamp": mem["timestamp"]
        }
        for mem in relevant_memory
    ]
    
    return {"search_results": search_results, "memory_context": relevant_memory}

def rag_context(state: ResearchState) -> Dict[str, Any]:
    """Retrieve relevant documents using RAG"""
    question = state["question"]
    logger.info(f"📚 Retrieving RAG context for: {question}")
    
    rag_docs = vector_store.similarity_search(question, Config.MAX_RAG_DOCS)
    
    return {"rag_docs": rag_docs}

def generate_answer(state: ResearchState) -> Dict[str, Any]:
    """Generate the final answer using OpenAI"""
    question = state["question"]
    search_results = state.get("search_results", [])
    rag_docs = state.get("rag_docs", [])
    memory_context = state.get("memory_context", [])
    
    logger.info(f"🤖 Generating answer for: {question}")
    
    # Build comprehensive context
    context_parts = []
    
    # Add search results
    if search_results:
        context_parts.append("## Search Results:")
        for i, result in enumerate(search_results[:3], 1):
            context_parts.append(f"{i}. **{result.get('title', 'Unknown')}**")
            context_parts.append(f"   Source: {result.get('url', result.get('source', 'Unknown'))}")
            context_parts.append(f"   Content: {result.get('snippet', '')}")
    
    # Add RAG documents
    if rag_docs:
        context_parts.append("\n## Related Documents:")
        for i, doc in enumerate(rag_docs, 1):
            context_parts.append(f"{i}. Source: {doc.get('source', 'Unknown')}")
            context_parts.append(f"   Content: {doc.get('content', '')[:200]}...")
    
    # Add memory context
    if memory_context:
        context_parts.append("\n## Previous Conversations:")
        for i, mem in enumerate(memory_context, 1):
            context_parts.append(f"{i}. Q: {mem['question']}")
            context_parts.append(f"   A: {mem['answer'][:100]}...")
    
    context = "\n".join(context_parts)
    
    # Create comprehensive prompt
    prompt = f"""
    You are a research assistant. Answer the following question using the provided context.
    
    Question: {question}
    
    Context:
    {context}
    
    Instructions:
    1. Provide a comprehensive answer based on the context
    2. Include specific citations using [Source: URL/Title] format
    3. If information is insufficient, mention what additional information would be helpful
    4. Be factual and acknowledge limitations in the available information
    
    Answer:
    """
    
    answer = OpenAIAPI.generate_response(prompt, max_tokens=1500)
    
    # Extract citations
    citations = []
    for result in search_results:
        if 'url' in result and result['url'] not in citations:
            citations.append(result['url'])
    
    return {"answer": answer, "citations": citations}

def update_memory(state: ResearchState) -> Dict[str, Any]:
    """Store the Q&A pair in memory for future reference"""
    question = state["question"]
    answer = state["answer"]
    citations = state.get("citations", [])
    
    logger.info(f"💾 Updating memory with Q&A")
    
    memory_store.add_entry(question, answer, citations)
    
    return {}

def should_continue_to_rag(state: ResearchState) -> str:
    """Conditional edge: determine if we should go to RAG or directly to answer"""
    tool_choice = state["tool_choice"]
    
    if tool_choice == ToolChoice.MEMORY_LOOKUP.value:
        return "generate_answer"
    else:
        return "rag_context"

def create_research_assistant():
    """Create and configure the research assistant graph"""
    
    # Create the StateGraph
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("receive_question", receive_question)
    graph.add_node("select_tool", select_tool)
    graph.add_node("web_search", web_search)
    graph.add_node("pdf_summarize", pdf_summarize)
    graph.add_node("memory_lookup", memory_lookup)
    graph.add_node("rag_context", rag_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("update_memory", update_memory)
    
    # Add edges
    graph.add_edge("receive_question", "select_tool")
    
    # Conditional edges from select_tool to different tools
    graph.add_conditional_edges(
        "select_tool",
        lambda state: state["tool_choice"],
        {
            ToolChoice.WEB_SEARCH.value: "web_search",
            ToolChoice.PDF_SUMMARIZE.value: "pdf_summarize",
            ToolChoice.MEMORY_LOOKUP.value: "memory_lookup"
        }
    )
    
    # Conditional edges to determine next step after tool execution
    graph.add_conditional_edges(
        "web_search",
        should_continue_to_rag,
        {
            "rag_context": "rag_context",
            "generate_answer": "generate_answer"
        }
    )
    
    graph.add_conditional_edges(
        "pdf_summarize",
        should_continue_to_rag,
        {
            "rag_context": "rag_context",
            "generate_answer": "generate_answer"
        }
    )
    
    graph.add_conditional_edges(
        "memory_lookup",
        should_continue_to_rag,
        {
            "rag_context": "rag_context",
            "generate_answer": "generate_answer"
        }
    )
    
    # From RAG to answer generation
    graph.add_edge("rag_context", "generate_answer")
    
    # From answer generation to memory update
    graph.add_edge("generate_answer", "update_memory")
    
    # From memory update to end
    graph.add_edge("update_memory", END)
    
    # Set entry point
    graph.set_entry_point("receive_question")
    
    return graph.compile()

# Example usage and testing
if __name__ == "__main__":
    # Check if API keys are configured
    if not Config.OPENAI_API_KEY:
        print("⚠️  Please set your OPENAI_API_KEY in the .env file")
        print("Get it from: https://platform.openai.com/api-keys")
        exit(1)
    
    if not Config.BRAVE_API_KEY:
        print("⚠️  Please set your BRAVE_API_KEY in the .env file")
        print("Get it from: https://brave.com/search/api/")
        exit(1)
    
    print("🚀 Starting Research Assistant...")
    print("📊 API Keys configured successfully")
    
    # Create the research assistant
    app = create_research_assistant()
    
    # Interactive mode
    print("\n🤖 Research Assistant is ready!")
    print("Ask me anything. Type 'quit' to exit.")
    print("Examples:")
    print("  - What are the latest developments in AI?")
    print("  - Search for recent news about climate change")
    print("  - Summarize this PDF: https://example.com/document.pdf")
    print("  - What did we discuss about Python earlier?")
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            print(f"\n🔄 Processing your question...")
            
            result = app.invoke({"question": question})
            
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n✅ Answer:")
                print(result["answer"])
                
                if result.get("citations"):
                    print(f"\n📚 Citations:")
                    for i, citation in enumerate(result["citations"], 1):
                        print(f"  {i}. {citation}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Unexpected error: {e}")