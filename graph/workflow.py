from langgraph.graph import StateGraph, START, END
from graph.state import PipelineState
from graph.nodes import (
    segregator_node, id_agent_node,
    discharge_agent_node, bill_agent_node,
    aggregator_node
)

def build_graph():
    builder = StateGraph(PipelineState)

    # Add Nodes
    builder.add_node("segregator", segregator_node)
    builder.add_node("id_agent", id_agent_node)
    builder.add_node("discharge_agent", discharge_agent_node)
    builder.add_node("bill_agent", bill_agent_node)
    builder.add_node("aggregator", aggregator_node)

    # Workflow Wiring
    builder.add_edge(START, "segregator")

    # Fan-out: segregator -> 3 specialist agents (parallel superstep)
    builder.add_edge("segregator", "id_agent")
    builder.add_edge("segregator", "discharge_agent")
    builder.add_edge("segregator", "bill_agent")

    # Fan-in: 3 agents -> aggregator (sync barrier)
    builder.add_edge("id_agent", "aggregator")
    builder.add_edge("discharge_agent", "aggregator")
    builder.add_edge("bill_agent", "aggregator")

    # End
    builder.add_edge("aggregator", END)

    return builder.compile()

# Singleton instance
graph = build_graph()
