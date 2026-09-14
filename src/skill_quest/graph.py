from skill_quest import config  # noqa: F401  (loads .env)

from langgraph.graph import END, START, StateGraph

from skill_quest.nodes import (
    run_goal_agent,
    run_research_agent,
    run_capability_agent,
    run_progression_planner,
    select_recommended_track,
    run_milestone_planner,
    finalize_planning,
    run_ladder_planner
)
from skill_quest.state import LearnerState


def build_graph(checkpointer=None):
    builder = StateGraph(LearnerState)

    builder.add_node("goal", run_goal_agent)
    builder.add_node("research", run_research_agent)
    builder.add_node("capability_mapper", run_capability_agent)
    builder.add_node("progression_plan", run_progression_planner)
    builder.add_node("select_recommended_track", select_recommended_track)
    builder.add_node("milestone_design", run_milestone_planner)
    builder.add_node("finalize_planning", finalize_planning)
    builder.add_node("ladder_architect", run_ladder_planner)

    builder.add_edge(START, "goal")
    builder.add_edge("goal", "research")
    builder.add_edge("research", "capability_mapper")
    builder.add_edge("capability_mapper", "progression_plan")
    builder.add_edge("progression_plan", "select_recommended_track")
    builder.add_edge("select_recommended_track", "milestone_design")
    builder.add_edge("milestone_design", "finalize_planning")
    builder.add_edge("finalize_planning", "ladder_architect")
    builder.add_edge("ladder_architect", END)

    return builder.compile(
        checkpointer=checkpointer,
    )

# Exported for langgraph dev / LangGraph API — the server supplies persistence.
graph = build_graph()

"""
I want to learn the electric guitar and pentatonic scales such that i can freely play them but with good melody sounds. and i want to learn the loop pedal so i can play back track harmony with my pentatonic blues rifting
"""