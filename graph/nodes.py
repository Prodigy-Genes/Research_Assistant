from langgraph.graph import StateGraph, END
from config import Config
from state import ResearchState, ToolChoice
from stores.vector_store import VectorStore
from stores.memory_store import MemoryStore
from api.brave_search import BraveSearchAPI
from api.openai_api import OpenAIAPI
from api.pdf_processor import PDFProcessor
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Initialize global instances
vector_store = VectorStore()
memory_store = MemoryStore()

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
    
    # Extract URL from question
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