from langgraph.graph import StateGraph, START, END
from state import LadderArchitectState
from nodes import ladder_architect_node

builder = StateGraph(LadderArchitectState)
builder.add_node("architect", ladder_architect_node)
builder.add_edge(START, "architect")
builder.add_edge("architect", END)

graph = builder.compile()
