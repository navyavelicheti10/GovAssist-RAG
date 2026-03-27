from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from govassist.agents.nodes import document_agent, llm_agent, rag_agent
from govassist.agents.state import AgentState


def route_from_start(state: AgentState) -> str:
    if state.get("input_type") == "document":
        return "DocumentAgent"
    return "LLMAgent"


def route_after_llm(state: AgentState) -> str:
    if state.get("rag_completed"):
        return END
    return "RAGAgent"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("LLMAgent", llm_agent)
    builder.add_node("RAGAgent", rag_agent)
    builder.add_node("DocumentAgent", document_agent)

    builder.add_conditional_edges(START, route_from_start)
    builder.add_edge("DocumentAgent", "LLMAgent")
    builder.add_conditional_edges("LLMAgent", route_after_llm)
    builder.add_edge("RAGAgent", "LLMAgent")

    return builder.compile(checkpointer=MemorySaver())


govassist_graph = build_graph()
vozhi_orchestrator = govassist_graph
