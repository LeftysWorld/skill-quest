from llm import architect_agent
from retrieval import retrieve_curriculum
from state import LadderArchitectState
from langchain_core.runnables import RunnableConfig


def ladder_architect_node(state: LadderArchitectState, config: RunnableConfig) -> LadderArchitectState:
    skill = state.get("skill", "unknown")
    template = state.get("ladder_template", "")

    chunks = retrieve_curriculum(skill, "progression, tiers, safety")

    prompt = f"""
Skill: {skill}
Ladder template:
{template}

Retrieved curriculum chunks:
{chr(10).join(chunks)}

Task: Generate Quest objects for the next appropriate nodes.
Return ONLY a JSON list of Quest objects.
"""

    try:
        result = architect_agent.run_sync(prompt)
        return {"draft_quests": result.output, "retrieved_chunks": chunks}
    except Exception as e:
        return {"error": str(e)}

