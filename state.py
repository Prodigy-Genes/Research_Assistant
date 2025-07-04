from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional

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