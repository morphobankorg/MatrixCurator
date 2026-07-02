from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from matrixcurator.modules.agent.state import AgentState, ContextSchema
from matrixcurator.modules.agent.nodes import (
    extractor_agent,
    evaluator_agent,
    supervisor_node,
)
from matrixcurator.modules.agent.memory import get_store


def build_graph():
    workflow = StateGraph(AgentState, config_schema=ContextSchema)

    # Add nodes
    workflow.add_node("extractor_agent", extractor_agent)
    workflow.add_node("evaluator_agent", evaluator_agent)
    workflow.add_node("supervisor_node", supervisor_node)

    # Add edges
    workflow.add_edge(START, "supervisor_node")
    workflow.add_edge("extractor_agent", "evaluator_agent")
    workflow.add_edge("evaluator_agent", "supervisor_node")

    # Compile
    checkpointer = MemorySaver()
    store = get_store()

    app = workflow.compile(checkpointer=checkpointer, store=store)
    return app


agent_graph = build_graph()
