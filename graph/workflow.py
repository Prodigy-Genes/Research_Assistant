from langgraph.graph import StateGraph, END
from .nodes import *
from state import ResearchState

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