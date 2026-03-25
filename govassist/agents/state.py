from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The state of the Vozhi orchestrator."""
    messages: Annotated[List[BaseMessage], add_messages]
    
    # User profile dynamically populated
    user_profile: Dict[str, Any]
    
    # Extracted fields from uploaded documents
    documents_extracted: Dict[str, Any]
    
    # Raw query info
    current_query: str
    
    # Schemes retrieved from Qdrant
    retrieved_schemes: List[Dict[str, Any]]
    
    # Synergies retrieved from Graph RAG
    synergy_schemes: List[str]
    
    # The final synthetic response
    final_package: str
    
    # Confidence score (0-100)
    confidence_score: float
    
    # List of citations
    citations: List[str]
