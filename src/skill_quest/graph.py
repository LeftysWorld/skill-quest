from skill_quest import config  # noqa: F401  (loads .env)

from langgraph.graph import END, START, StateGraph

from skill_quest.nodes import run_goal_agent, run_research_agent
from skill_quest.state import LearnerState


def build_graph(checkpointer=None):
    builder = StateGraph(LearnerState)

    builder.add_node("goal", run_goal_agent)
    builder.add_node("research", run_research_agent)

    builder.add_edge(START, "goal")
    builder.add_edge("goal", "research")
    builder.add_edge("research", END)

    return builder.compile(checkpointer=checkpointer)


# Exported for langgraph dev / LangGraph API — the server supplies persistence.
graph = build_graph()

"""
I want to learn the electric guitar and pentonic scales such that i can freely play them but with good melody sounds. and i want to learn the loop pedal so i can play back track harmony with my pentonic blues rifting
"""