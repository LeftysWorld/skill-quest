from dotenv import load_dotenv
load_dotenv()

from dataclasses import dataclass
from typing import Any, Dict, Literal, List
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

tavily_client = TavilyClient()

# ---------- Tools ----------

@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information."""
    return tavily_client.search(query)

# ---------- Input schema ----------

@dataclass
class CurriculumContext:
    skill: str = "electric guitar"
    learner_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    available_minutes_per_day: int = 30
    equipment: str = (
        "electric guitar, amplifier, cable, tuner, picks, and strap"
    )


# ---------- Ladder (derived internally) ----------

@dataclass
class Ladder:
    id: str
    skill: str
    level: str
    created_at: str


def make_ladder_from_context(ctx: CurriculumContext) -> Ladder:
    """
    Derive a Ladder from CurriculumContext.
    For now, ladder_id is just a simple slug: skill-level-001
    """
    slug = f"{ctx.skill.lower().replace(' ', '-')}-{ctx.learner_level}-001"
    return Ladder(
        id=slug,
        skill=ctx.skill,
        level=ctx.learner_level,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

# ---------- Output schema ----------

class Quest(BaseModel):
    id: str = Field(..., description="Unique quest identifier, e.g. 'Q1', 'Q2', ...")
    ladder_id: str = Field(..., description="ID of the ladder this quest belongs to")
    tier: int = Field(..., description="Tier in the ladder, 0-5")
    title: str
    completion_condition: str
    evidence_required: list[Literal["photo", "video", "audio", "reading", "gps", "witness", "note"]]
    twist: str
    difficulty: Literal["easy", "real", "wild"]


class QuestList(BaseModel):
    quests: List[Quest] = Field(..., description="List of curriculum quests")


# ---------- Prompt (middleware) ----------

@dynamic_prompt
def curriculum_prompt(request: ModelRequest) -> str:
    """
    Build the system prompt from CurriculumContext.
    Internally derive a Ladder and tell the model:
      - which ladder we're designing
      - that each quest must include ladder_id and tier
    """
    ctx: CurriculumContext = request.runtime.context
    ladder = make_ladder_from_context(ctx)

    return f"""
You are an expert curriculum designer.

Ladder ID: {ladder.id}
Skill: {ladder.skill}
Level: {ladder.level}
Available practice time: {ctx.available_minutes_per_day} minutes per day
Equipment: {ctx.equipment}

Your task: design a beginner-to-advanced progression ladder as exactly 6 Quest objects.

For each Quest, provide:
- id (e.g. "Q1", "Q2", ... "Q6")
- ladder_id (must be exactly: {ladder.id})
- tier (0 for the first quest, 1 for the second, ..., 5 for the last)
- title
- completion_condition
- evidence_required (choose from: photo, video, audio, reading, gps, witness, note)
- twist (a small constraint that makes it feel designed)
- difficulty (easy, real, or wild)

Make the progression realistic, cumulative, and safety-conscious.
Use web search when current or source-based research would improve the answer.
When you use web search, base recommendations on retrieved sources.

Return ONLY a JSON object with a single key "quests" whose value is a list of Quest objects.
Do not include any explanation or extra text.
"""

# ---------- Agent ----------

agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    context_schema=CurriculumContext,
    middleware=[curriculum_prompt],
    response_format=QuestList,
)

# ---------- Main ----------

if __name__ == "__main__":
    # This block is just a local test harness.
    # Vercel Agent Chat / LangSmith will call the agent with their own context
    # (or defaults) when you interact via the UI.

    curriculum_context = CurriculumContext(
        skill="electric guitar",
        learner_level="beginner",
        available_minutes_per_day=30,
        equipment=(
            "electric guitar, amplifier, cable, tuner, picks, and strap"
        ),
    )

    response = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Create a beginner-to-advanced progression ladder."
                )
            ]
        },
        context=curriculum_context,
    )

    # Extract structured output (QuestList)
    quest_list = response.get("output")
    if quest_list is None:
        last_msg = response.get("messages", [])[-1]
        quest_list = last_msg.additional_kwargs.get("structured_output")

    if quest_list is None:
        from pprint import pprint
        pprint(response)
        raise RuntimeError("Structured output not found; inspect response above.")

    # quest_list is a QuestList instance
    ladder_id = quest_list.quests[0].ladder_id if quest_list.quests else "unknown"
    print("Ladder:", ladder_id)
    print("Number of quests:", len(quest_list.quests))
    for q in quest_list.quests:
        print(f"Tier {q.tier} | {q.id} | {q.title} | {q.difficulty}")

#  id like there to be more. something like several quests to get to a skill. maybe a week long or a couple weeks long. then to pass i might need to demonstrate it.
