from langgraph.graph import StateGraph, START, END
from govassist.agents.state import AgentState
from govassist.agents.nodes import profile_agent, document_agent, retrieval_agent, synthesis_agent
from langgraph.checkpoint.memory import MemorySaver

def build_graph():
    """Builds and compiles the Vozhi Multi-Agent Graph."""
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("ProfileAgent", profile_agent)
    builder.add_node("DocumentAgent", document_agent)
    builder.add_node("RetrievalAgent", retrieval_agent)
    builder.add_node("SynthesisAgent", synthesis_agent)
    
    # Define Edges
    builder.add_edge(START, "ProfileAgent")
    builder.add_edge("ProfileAgent", "DocumentAgent")
    builder.add_edge("DocumentAgent", "RetrievalAgent")
    builder.add_edge("RetrievalAgent", "SynthesisAgent")
    builder.add_edge("SynthesisAgent", END)
    
    # Compile Graph
    memory = MemorySaver()
    app = builder.compile(checkpointer=memory)
    
    return app

vozhi_orchestrator = build_graph()
