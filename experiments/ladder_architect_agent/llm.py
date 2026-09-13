from pydantic_ai import Agent
from models import Quest

architect_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=list[Quest],
    instructions="""
You are a Ladder Architect for real-world skill ladders.
You must return ONLY a JSON list of Quest objects.
Every quest must have: title, completion_condition, evidence_required, twist, difficulty.
Use the provided ladder template and retrieved curriculum chunks as sources.
Do not invent places or resources; only use what is provided.
""",
)
